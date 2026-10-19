"""Phase 1 synthetic data generator (temporarystand-in for friends' real collection).

Contract matches Docs/data.md D1-D4 + D5/D6 seeds. Deterministic (seed=42).
Grain: 5 generic wards x daily 2024-01-01..2025-12-31 (731 days, 2024 leap).
Units: water in ML. 1 MCM = 1000 ML.
"""

from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
START = "2024-01-01"
END = "2025-12-31"
LPCD = 135.0  # CPHEEO norm, litres per capita per day

WARDS = [
    {"ward_id": "W001", "ward_name": "Ward A", "base_pop": 50000, "area_km2": 4.2, "growth": 0.022},
    {"ward_id": "W002", "ward_name": "Ward B", "base_pop": 38000, "area_km2": 3.1, "growth": 0.028},
    {"ward_id": "W003", "ward_name": "Ward C", "base_pop": 62000, "area_km2": 5.0, "growth": 0.018},
    {"ward_id": "W004", "ward_name": "Ward D", "base_pop": 29000, "area_km2": 2.4, "growth": 0.031},
    {"ward_id": "W005", "ward_name": "Ward E", "base_pop": 45000, "area_km2": 3.8, "growth": 0.025},
]

RESERVOIRS = [
    {
        "reservoir_id": "R01",
        "reservoir_name": "North Reservoir",
        "lat": 12.98,
        "lon": 77.59,
        "capacity_mcm": 12.0,
        "base_avail_ml": 25.0,
        "serving": ["W001", "W002", "W003"],
    },
    {
        "reservoir_id": "R02",
        "reservoir_name": "South Reservoir",
        "lat": 12.93,
        "lon": 77.62,
        "capacity_mcm": 8.0,
        "base_avail_ml": 15.0,
        "serving": ["W004", "W005"],
    },
]


def season_of(month: int) -> str:
    if month in (3, 4, 5, 6):
        return "Summer"
    if month in (7, 8, 9):
        return "Monsoon"
    if month in (10, 11):
        return "PostMonsoon"
    return "Winter"


def seasonal_factor(month: int) -> float:
    return {"Summer": 1.20, "Monsoon": 0.95, "PostMonsoon": 1.02, "Winter": 0.90}[season_of(month)]


def generate_population() -> tuple[pd.DataFrame, pd.DataFrame]:
    ward_rows = [
        {"ward_id": w["ward_id"], "ward_name": w["ward_name"], "area_km2": w["area_km2"]} for w in WARDS
    ]
    pop_rows = []
    for w in WARDS:
        for year in (2022, 2023, 2024, 2025):
            pop = int(round(w["base_pop"] * (1 + w["growth"]) ** (year - 2023)))
            pop_rows.append(
                {
                    "ward_id": w["ward_id"],
                    "ward_name": w["ward_name"],
                    "year": year,
                    "population": pop,
                    "area_km2": w["area_km2"],
                    "density": round(pop / w["area_km2"], 1),
                    "growth_pct": round(w["growth"] * 100, 2),
                }
            )
    return pd.DataFrame(ward_rows), pd.DataFrame(pop_rows)


def generate_consumption(pop: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    dates = pd.date_range(START, END, freq="D")
    pop2024 = {r.ward_id: r.population for r in pop[pop.year == 2024].itertuples()}
    pop2025 = {r.ward_id: r.population for r in pop[pop.year == 2025].itertuples()}
    rows = []
    for w in WARDS:
        wid = w["ward_id"]
        for d in dates:
            pop_now = pop2024[wid] if d.year == 2024 else pop2025[wid]
            base_ml = pop_now * LPCD / 1e6
            dow = d.dayofweek
            weekend = 1 if dow >= 5 else 0
            seasonal = seasonal_factor(d.month)
            weekend_f = 1.05 if weekend else 1.0
            trend = 1.0 + 0.00003 * (d - dates[0]).days  # slight within-period drift
            noise = float(rng.normal(0, 0.03))
            # occasional heatwave spikes in summer
            spike = 1.12 if (season_of(d.month) == "Summer" and rng.random() < 0.04) else 1.0
            demand = round(base_ml * seasonal * weekend_f * trend * spike * (1 + noise), 4)
            # supplied tracks demand with shortfalls (worse in summer peaks)
            shortfall = 0.06 if season_of(d.month) == "Summer" else 0.02
            supplied = round(demand * float(rng.normal(1 - shortfall, 0.03)), 4)
            supplied = max(supplied, round(demand * 0.70, 4))
            loss_rate = float(rng.uniform(0.08, 0.15))
            consumed = round(supplied * (1 - loss_rate), 4)
            rows.append(
                {
                    "date": d.strftime("%Y-%m-%d"),
                    "ward_id": wid,
                    "demand_ml": demand,
                    "water_supplied_ml": supplied,
                    "water_consumed_ml": consumed,
                }
            )
    df = pd.DataFrame(rows).sort_values(["ward_id", "date"]).reset_index(drop=True)
    return df


def generate_reservoirs(dates: pd.DatetimeIndex) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(SEED + 1)
    res_rows = [
        {
            "reservoir_id": r["reservoir_id"],
            "reservoir_name": r["reservoir_name"],
            "lat": r["lat"],
            "lon": r["lon"],
            "capacity_mcm": r["capacity_mcm"],
            "serving_wards": ";".join(r["serving"]),
        }
        for r in RESERVOIRS
    ]
    read_rows = []
    for r in RESERVOIRS:
        for d in dates:
            # storage depletes through summer, recovers in monsoon
            if season_of(d.month) == "Summer":
                storage_frac = float(rng.normal(0.52, 0.10))
            elif season_of(d.month) == "Monsoon":
                storage_frac = float(rng.normal(0.85, 0.07))
            else:
                storage_frac = float(rng.normal(0.68, 0.08))
            storage_frac = float(np.clip(storage_frac, 0.25, 0.98))
            current_mcm = round(r["capacity_mcm"] * storage_frac, 3)
            # available water for the day scales with storage + noise; engineered so
            # WAR spans Safe..Shortage across the 2-year window
            avail = r["base_avail_ml"] * (0.55 + 0.65 * storage_frac) * float(rng.normal(1, 0.05))
            # force ~5% shortage-dip days in peak summer
            if season_of(d.month) == "Summer" and rng.random() < 0.05:
                avail *= 0.70
            read_rows.append(
                {
                    "date": d.strftime("%Y-%m-%d"),
                    "reservoir_id": r["reservoir_id"],
                    "level_m": round(10 + storage_frac * 18, 2),
                    "capacity_mcm": r["capacity_mcm"],
                    "current_storage_mcm": current_mcm,
                    "storage_pct": round(storage_frac * 100, 2),
                    "available_water_ml": round(max(avail, 1.0), 3),
                }
            )
    return pd.DataFrame(res_rows), pd.DataFrame(read_rows).sort_values(
        ["reservoir_id", "date"]
    ).reset_index(drop=True)


def generate_maintenance(consumption: pd.DataFrame) -> pd.DataFrame:
    rng = random.Random(SEED + 2)
    sample = consumption.sample(n=60, random_state=SEED).sort_values(["ward_id", "date"])
    kinds = ["burst", "leak", "valve", "quality"]
    rows = []
    for i, r in enumerate(sample.itertuples(), 1):
        rows.append(
            {
                "incident_id": f"M{i:04d}",
                "date": r.date,
                "ward_id": r.ward_id,
                "incident_type": rng.choice(kinds),
                "cause": rng.choice(["aging-pipe", "pressure", "construction", "unknown"]),
                "severity": rng.choice(["low", "medium", "high"]),
                "resolved_date": r.date,
            }
        )
    return pd.DataFrame(rows)


def generate_wards_geojson() -> str:
    # Approximate 5-cell grid over a small bbox; labeled approximate per data.md.
    import json

    polys = {
        "W001": [[77.55, 12.95], [77.58, 12.95], [77.58, 12.98], [77.55, 12.98], [77.55, 12.95]],
        "W002": [[77.58, 12.95], [77.61, 12.95], [77.61, 12.98], [77.58, 12.98], [77.58, 12.95]],
        "W003": [[77.55, 12.98], [77.58, 12.98], [77.58, 13.01], [77.55, 13.01], [77.55, 12.98]],
        "W004": [[77.58, 12.98], [77.61, 12.98], [77.61, 13.01], [77.58, 13.01], [77.58, 12.98]],
        "W005": [[77.61, 12.95], [77.64, 12.95], [77.64, 13.01], [77.61, 13.01], [77.61, 12.95]],
    }
    features = [
        {
            "type": "Feature",
            "properties": {"ward_id": wid, "provenance": "synthetic-approximate"},
            "geometry": {"type": "Polygon", "coordinates": [coords]},
        }
        for wid, coords in polys.items()
    ]
    return json.dumps({"type": "FeatureCollection", "features": features}, indent=2)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    raw = root / "data" / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    wards, pop = generate_population()
    consumption = generate_consumption(pop)
    dates = pd.date_range(START, END, freq="D")
    reservoirs, readings = generate_reservoirs(dates)
    maintenance = generate_maintenance(consumption)

    wards.to_csv(raw / "wards.csv", index=False)
    pop.to_csv(raw / "population.csv", index=False)
    consumption.to_csv(raw / "consumption.csv", index=False)
    reservoirs.to_csv(raw / "reservoirs.csv", index=False)
    readings.to_csv(raw / "reservoir_readings.csv", index=False)
    maintenance.to_csv(raw / "maintenance.csv", index=False)
    (raw / "wards.geojson").write_text(generate_wards_geojson())

    print(f"wards={len(wards)} pop={len(pop)} consumption={len(consumption)} "
          f"readings={len(readings)} maintenance={len(maintenance)}")
    print(f"wards={sorted(consumption.ward_id.unique().tolist())} "
          f"dates={consumption.date.min()}..{consumption.date.max()}")


if __name__ == "__main__":
    main()
