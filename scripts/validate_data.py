"""Phase 1 gate: validate any dataset (synthetic now, real at swap) meets the contract."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1] / "data" / "raw"


def check() -> list[str]:
    errors: list[str] = []
    c = pd.read_csv(ROOT / "consumption.csv")
    p = pd.read_csv(ROOT / "population.csv")
    r = pd.read_csv(ROOT / "reservoir_readings.csv")
    w = pd.read_csv(ROOT / "wards.csv")

    if c.duplicated(["ward_id", "date"]).sum():
        errors.append("duplicate ward-date rows in consumption.csv")
    if sorted(c.ward_id.unique()) != sorted(w.ward_id.unique()):
        errors.append("ward mismatch consumption vs wards")
    if set(c.ward_id.unique()) - set(p.ward_id.unique()):
        errors.append("consumption wards missing from population")
    if int(c.isna().sum().sum() + r.isna().sum().sum() + p.isna().sum().sum()):
        errors.append("nulls present")
    if not ((r.current_storage_mcm / r.capacity_mcm * 100 - r.storage_pct).abs() < 0.011).all():
        errors.append("storage_pct formula broken")
    if not ((p.population / p.area_km2 - p.density).abs() < 0.06).all():
        errors.append("density formula broken")
    if len(c) < 5 * 365:
        errors.append("insufficient daily coverage (need >=1yr/ward)")
    return errors


if __name__ == "__main__":
    errs = check()
    print("PASS" if not errs else "FAIL: " + "; ".join(errs))
    sys.exit(1 if errs else 0)
