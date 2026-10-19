"""Smart supply planner (Phase 8 + Advanced LP follow-up).

Per reservoir pool: pool = total_available * (1 - reserve_pct).
Engines (env SUPPLY_OPTIMIZER=rule|lp, default rule):
- rule: severity-weighted pro-rata to forecast, capped at forecast, with
  iterative redistribution of leftover (water-filling).
- lp (`planner_lp.alloc_lp`): PuLP/CBC optimum of the same contract.
Guarantees (both engines):
  sum(allocated) == min(pool, sum(forecast))  (never over-allocates; surplus stays stored)
  no ward exceeds its forecast (no waste)
  higher-severity wards get proportionally more (weights 4/3/2/1)
Alert: pre-allocation category in (High Stress, Shortage).
"""

import datetime as dt

from sqlalchemy.orm import Session

from app import inference, models, stress
from app.config import settings

SEVERITY_RANK = {"Shortage": 0, "High Stress": 1, "Moderate": 2, "Safe": 3}
SEVERITY_WEIGHT = {0: 4.0, 1: 3.0, 2: 2.0, 3: 1.0}
ALERT_CATEGORIES = {"High Stress", "Shortage"}


def alloc(pool: float, forecasts: list[float], ranks: list[int]) -> list[float]:
    """Pure function: split pool across wards. Unit-tested without DB."""
    n = len(forecasts)
    weights = [SEVERITY_WEIGHT[r] * f for r, f in zip(ranks, forecasts)]
    denom = sum(weights)
    if denom <= 0 or pool <= 0:
        return [0.0] * n
    awarded = [pool * w / denom for w in weights]
    capped = [min(a, f) for a, f in zip(awarded, forecasts)]
    # Redistribute leftover from capped wards, pro-rata among uncapped.
    for _ in range(n + 1):
        leftover = pool - sum(capped)
        if leftover < 1e-9:
            break
        open_idx = [i for i in range(n) if capped[i] < forecasts[i] - 1e-9]
        if not open_idx:
            break
        wsum = sum(weights[i] for i in open_idx)
        if wsum <= 0:
            break
        for i in open_idx:
            capped[i] = min(forecasts[i], capped[i] + leftover * weights[i] / wsum)
    # Round for persistence, then repair sub-litre rounding dust (never beyond
    # forecast caps; large residuals = genuine surplus and are left stored).
    rounded = [round(a, 4) for a in capped]
    drift = round(pool - sum(rounded), 4)
    if 0 < abs(drift) < 0.01:
        for i in sorted(range(n), key=lambda j: (-weights[j], j)):
            if drift == 0:
                break
            if drift > 0:
                headroom = round(forecasts[i] - rounded[i], 4)
                add = min(drift, headroom)
                rounded[i] = round(rounded[i] + add, 4)
                drift = round(drift - add, 4)
            elif rounded[i] > 0:
                take = min(-drift, rounded[i])
                rounded[i] = round(rounded[i] - take, 4)
                drift = round(drift + take, 4)
    return rounded


def plan_for_date(db: Session, date: dt.date, horizon: str = "1d",
                  reserve_pct: float | None = None) -> dict:
    reserve_pct = settings.supply_reserve_pct if reserve_pct is None else reserve_pct
    wards_out: list[dict] = []
    pools: list[dict] = []
    for res in db.query(models.Reservoir).order_by(models.Reservoir.reservoir_id).all():
        served = [s.strip() for s in res.serving_wards.split(";") if s.strip()]
        reading = db.query(models.ReservoirReading).filter_by(
            reservoir_id=res.reservoir_id, date=date).first()
        if not reading:
            continue
        pool = round(reading.available_water_ml * (1 - reserve_pct), 4)
        forecasts, ranks, cats = [], [], []
        for wid in served:
            s = stress.compute(db, wid, date, horizon)
            forecasts.append(s["forecast_ml"])
            ranks.append(SEVERITY_RANK[s["category"]])
            cats.append(s["category"])
        awarded = alloc(pool, forecasts, ranks)
        if settings.supply_optimizer == "lp":
            from app import planner_lp
            awarded = planner_lp.alloc_lp(pool, forecasts, ranks)
        pools.append({"reservoir_id": res.reservoir_id, "pool_ml": pool,
                      "reserve_pct": reserve_pct})
        for wid, fc, cat, got in zip(served, forecasts, cats, awarded):
            alert = cat in ALERT_CATEGORIES
            if horizon == "1d":
                db.merge(models.SupplyPlan(ward_id=wid, date=date,
                                           allocated_ml=got, alert=alert))
            wards_out.append({"ward_id": wid, "reservoir_id": res.reservoir_id,
                              "forecast_ml": fc, "category": cat,
                              "allocated_ml": got, "alert": alert})
    db.commit()
    total_alloc = round(sum(w["allocated_ml"] for w in wards_out), 4)
    return {"date": date.isoformat(), "horizon": horizon,
            "reserve_pct": reserve_pct, "pools": pools,
            "wards": sorted(wards_out, key=lambda w: w["ward_id"]),
            "total_allocated_ml": total_alloc}
