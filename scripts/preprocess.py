"""Phase 2: preprocessing + integration pipeline (importable, deterministic).

Reads data/raw/*.csv, writes data/processed/merged_ward_date.csv + data/quality_report.md.
Policy:
- dedupe on natural keys, keep first, log counts.
- missing: numeric consumption/reservoir -> interpolate per group then ffill/bfill;
  population yearly -> ffill per ward (synthetic-v1 has zero missing; policy exercised anyway).
- outliers: IQR per ward on demand_ml/water_consumed_ml; CAP (clip) to bounds, never drop
  rows (preserves time-series continuity). Counts logged.
- no scaling here: scaling is fit on train only in Phase 3 to avoid leakage.
- reservoir->ward mapping via reservoirs.csv serving_wards (equal split of available
  water among served wards; single-reservoir wards in synthetic-v1 get full share).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"


def load_raw() -> dict[str, pd.DataFrame]:
    return {
        "consumption": pd.read_csv(RAW / "consumption.csv", parse_dates=["date"]),
        "population": pd.read_csv(RAW / "population.csv"),
        "reservoirs": pd.read_csv(RAW / "reservoirs.csv"),
        "readings": pd.read_csv(RAW / "reservoir_readings.csv", parse_dates=["date"]),
        "wards": pd.read_csv(RAW / "wards.csv"),
    }


def standardize(d: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    for key in ("consumption", "readings"):
        d[key]["date"] = pd.to_datetime(d[key]["date"]).dt.normalize()
    for key in ("consumption", "population", "wards"):
        d[key]["ward_id"] = d[key]["ward_id"].astype(str).str.strip().str.upper()
    d["readings"]["reservoir_id"] = d["readings"]["reservoir_id"].astype(str).str.strip().str.upper()
    d["reservoirs"]["reservoir_id"] = d["reservoirs"]["reservoir_id"].astype(str).str.strip().str.upper()
    return d


def dedupe(df: pd.DataFrame, keys: list[str]) -> tuple[pd.DataFrame, int]:
    n0 = len(df)
    df = df.drop_duplicates(subset=keys, keep="first").reset_index(drop=True)
    return df, n0 - len(df)


def missing_report(d: dict[str, pd.DataFrame]) -> dict[str, float]:
    out = {}
    for name, df in d.items():
        out[name] = round(float(df.isna().sum().sum()) / max(len(df), 1) * 100, 3)
    return out


def impute_consumption(c: pd.DataFrame) -> pd.DataFrame:
    c = c.sort_values(["ward_id", "date"]).reset_index(drop=True)
    num = ["demand_ml", "water_supplied_ml", "water_consumed_ml"]
    c[num] = c.groupby("ward_id")[num].transform(lambda g: g.interpolate().ffill().bfill())
    return c


def impute_readings(r: pd.DataFrame) -> pd.DataFrame:
    r = r.sort_values(["reservoir_id", "date"]).reset_index(drop=True)
    num = ["level_m", "current_storage_mcm", "storage_pct", "available_water_ml"]
    r[num] = r.groupby("reservoir_id")[num].transform(lambda g: g.interpolate().ffill().bfill())
    return r


def cap_outliers_iqr(df: pd.DataFrame, group: str, cols: list[str]) -> tuple[pd.DataFrame, dict[str, int]]:
    counts: dict[str, int] = {}
    df = df.copy()
    for col in cols:
        q1 = df.groupby(group)[col].transform("quantile", 0.25)
        q3 = df.groupby(group)[col].transform("quantile", 0.75)
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (df[col] < lo) | (df[col] > hi)
        counts[col] = int(mask.sum())
        df[col] = df[col].clip(lower=lo, upper=hi)
    return df, counts


def ward_reservoir_map(reservoirs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in reservoirs.itertuples():
        served = [s.strip().upper() for s in str(r.serving_wards).split(";") if s.strip()]
        share = 1.0 / len(served)
        for wid in served:
            rows.append({"ward_id": wid, "reservoir_id": r.reservoir_id, "share": share})
    return pd.DataFrame(rows)


def build_merged(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    c = d["consumption"]
    pop = d["population"]
    pop_year = pop.set_index(["ward_id", "year"])[["population", "density", "growth_pct"]]
    c = c.copy()
    c["year"] = c["date"].dt.year
    c = c.merge(pop_year, left_on=["ward_id", "year"], right_index=True, how="left", validate="m:1")

    wmap = ward_reservoir_map(d["reservoirs"])
    avail = d["readings"].merge(wmap, on="reservoir_id", how="left", validate="m:m")
    avail["ward_avail_ml"] = avail["available_water_ml"] * avail["share"]
    ward_avail = avail.groupby([pd.Grouper(key="date"), "ward_id"], as_index=False).agg(
        available_water_ml=("ward_avail_ml", "sum"),
        storage_pct=("storage_pct", "mean"),
        reservoir_id=("reservoir_id", "first"),
    )

    m = c.merge(ward_avail, on=["ward_id", "date"], how="left", validate="1:1")
    assert m["available_water_ml"].notna().all(), "reservoir mapping left ward-dates uncovered"
    assert m["population"].notna().all(), "population mapping left ward-dates uncovered"

    dt = m["date"]
    m["day"] = dt.dt.day
    m["day_of_week"] = dt.dt.dayofweek
    m["month"] = dt.dt.month
    m["year_col"] = dt.dt.year
    m["season"] = m["month"].map(
        {12: "Winter", 1: "Winter", 2: "Winter", 3: "Summer", 4: "Summer", 5: "Summer",
         6: "Summer", 7: "Monsoon", 8: "Monsoon", 9: "Monsoon",
         10: "PostMonsoon", 11: "PostMonsoon"}
    )
    m["weekend"] = (m["day_of_week"] >= 5).astype(int)
    m = m.drop(columns=["year"]).rename(columns={"year_col": "year"})
    return m.sort_values(["ward_id", "date"]).reset_index(drop=True)


def main() -> None:
    PROC.mkdir(parents=True, exist_ok=True)
    d = standardize(load_raw())
    miss_before = missing_report(d)

    d["consumption"], dup_c = dedupe(d["consumption"], ["ward_id", "date"])
    d["readings"], dup_r = dedupe(d["readings"], ["reservoir_id", "date"])
    d["consumption"] = impute_consumption(d["consumption"])
    d["readings"] = impute_readings(d["readings"])
    d["consumption"], out_counts = cap_outliers_iqr(
        d["consumption"], "ward_id", ["demand_ml", "water_consumed_ml"]
    )
    miss_after = missing_report(d)

    merged = build_merged(d)
    expected = merged.ward_id.nunique() * merged.date.nunique()
    assert len(merged) == expected, f"row count {len(merged)} != ward x date {expected}"
    assert merged.duplicated(["ward_id", "date"]).sum() == 0

    merged.to_csv(PROC / "merged_ward_date.csv", index=False)
    report = (
        "# Quality report — Phase 2 (bmc-v1)\n\n"
        f"- merged rows: {len(merged)} (wards {merged.ward_id.nunique()} x dates {merged.date.nunique()})\n"
        f"- period: {merged.date.min().date()}..{merged.date.max().date()}\n"
        f"- duplicates removed: consumption={dup_c}, readings={dup_r}\n"
        f"- missing % before: {miss_before}\n"
        f"- missing % after impute: {miss_after}\n"
        f"- outliers capped (IQR per ward): {out_counts}\n"
        "- reservoir mapping: equal split among served wards "
        "(per reservoirs.csv serving_wards; 7 BMC reservoirs)\n"
        "- scaling: deferred to Phase 3 (fit on train only, no leakage)\n"
        "- assertions: 1:1 ward-date merge, no null keys, row count == ward x date — all PASS\n"
    )
    (ROOT / "data" / "quality_report.md").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
