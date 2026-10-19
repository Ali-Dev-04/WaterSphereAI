"""Drift guard (cron-ready): compares live forecast error against the registry.

Joins persisted forecasts (`Forecast`, written by /api/forecast) with realized
consumption (`Consumption`) over the trailing 30 days per horizon and compares
MAPE to the test MAPE pinned in models/manifest.json.
Exit 0 = healthy; exit 1 = drift (validation MAPE regressed >1pt → retrain).
Suggested cron: monthly, day 1 03:00. See EVALUATION.md §7.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

def _root() -> Path:
    cands = []
    if os.environ.get("WS_ROOT"):
        cands.append(Path(os.environ["WS_ROOT"]))
    try:
        cands.append(Path(__file__).resolve().parents[1])
    except Exception:
        pass
    cands.append(Path("/code"))
    for c in cands:
        if (c / "models" / "manifest.json").exists():
            return c
    return cands[0] if cands else Path("/code")


ROOT = _root()
sys.path.insert(0, str(ROOT / "backend"))

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://watersphere:devpass@localhost:5433/watersphere")

THRESHOLD_PTS = 1.0
WINDOW_DAYS = 30


def main() -> int:
    from app import models  # noqa: E402

    manifest = json.loads((ROOT / "models" / "manifest.json").read_text())
    pinned = {h: manifest["metrics"]["test"][manifest["active_per_horizon"][h]][h]["mape"]
              for h in ("1d", "3d", "7d")}
    eng = create_engine(DATABASE_URL)
    drifted: list[str] = []
    with Session(eng) as db:
        for h in ("1d", "3d", "7d"):
            rows = (db.query(models.Forecast, models.Consumption)
                    .join(models.Consumption,
                          (models.Consumption.ward_id == models.Forecast.ward_id)
                          & (models.Consumption.date == models.Forecast.target_date))
                    .filter(models.Forecast.horizon == h,
                            models.Forecast.target_date >= dt.date.today()
                            - dt.timedelta(days=WINDOW_DAYS)).all())
            if len(rows) < 10:
                print(f"{h}: only {len(rows)} scored forecasts in window — skip (need ≥10)")
                continue
            mape = sum(abs((c.demand_ml - f.predicted_ml) / max(c.demand_ml, 1e-9))
                          for f, c in rows) / len(rows) * 100
            status = "DRIFT" if mape - pinned[h] > THRESHOLD_PTS else "ok"
            print(f"{h}: live MAPE {mape:.2f}% vs pinned {pinned[h]:.2f}% → {status} (n={len(rows)})")
            if status == "DRIFT":
                drifted.append(h)
    if drifted:
        print(f"DRIFT on {drifted}: retrain out of cycle (monthly cron + EVALUATION.md §7)")
        return 1
    print("no drift: live error within 1pt of pinned test MAPE (or insufficient scored forecasts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
