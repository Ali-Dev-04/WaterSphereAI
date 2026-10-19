"""Phase 3: feature engineering + chronological train/val/test splits (no leakage).

Inputs: data/processed/merged_ward_date.csv
Outputs: features.csv, train.csv, val.csv, test.csv, split_meta.json,
         scaler.json (fit on train only), eda_report.md
Rules: all past features use shift(1) minimum, computed PER WARD; targets are
future demand per ward (t+1/3/7); split is chronological by date (70/15/15).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"

FEATURE_COLS = [
    "population", "density", "growth_pct",
    "lag_1", "lag_7", "lag_30", "roll_7", "roll_30",
    "available_water_ml", "storage_pct",
    "day", "day_of_week", "month", "year", "weekend",
]
TARGETS = ["target_1d", "target_3d", "target_7d"]


def add_features(m: pd.DataFrame) -> pd.DataFrame:
    m = m.sort_values(["ward_id", "date"]).reset_index(drop=True)
    g = m.groupby("ward_id")["demand_ml"]
    m["lag_1"] = g.transform(lambda s: s.shift(1))
    m["lag_7"] = g.transform(lambda s: s.shift(7))
    m["lag_30"] = g.transform(lambda s: s.shift(30))
    m["roll_7"] = g.transform(lambda s: s.shift(1).rolling(7, min_periods=7).mean())
    m["roll_30"] = g.transform(lambda s: s.shift(1).rolling(30, min_periods=30).mean())
    m["target_1d"] = g.transform(lambda s: s.shift(-1))
    m["target_3d"] = g.transform(lambda s: s.shift(-3))
    m["target_7d"] = g.transform(lambda s: s.shift(-7))
    season_dummies = pd.get_dummies(m["season"], prefix="season", dtype=float)
    m = pd.concat([m, season_dummies], axis=1)
    return m


def leakage_spot_check(df: pd.DataFrame) -> None:
    """Recompute one rolling value by hand; fail if feature used future info."""
    w = df.ward_id.unique()[0]
    sub = df[df.ward_id == w].sort_values("date").reset_index(drop=True)
    row = sub.iloc[40]  # has full 30-day window, not in tail
    prior7 = sub.loc[33:39, "demand_ml"].tolist()  # 7 rows strictly before row 40
    assert len(prior7) == 7
    assert abs(row["roll_7"] - float(np.mean(prior7))) < 1e-9, "roll_7 leakage check failed"


def main() -> None:
    merged = pd.read_csv(PROC / "merged_ward_date.csv", parse_dates=["date"])
    feat = add_features(merged)
    n0 = len(feat)
    feat = feat.dropna(subset=["lag_1", "lag_7", "lag_30", "roll_7", "roll_30"] + TARGETS)
    feat = feat.reset_index(drop=True)
    leakage_spot_check(feat)

    dates = sorted(feat.date.unique())
    n = len(dates)
    cut1, cut2 = dates[int(n * 0.70)], dates[int(n * 0.85)]
    train = feat[feat.date < cut1].reset_index(drop=True)
    val = feat[(feat.date >= cut1) & (feat.date < cut2)].reset_index(drop=True)
    test = feat[feat.date >= cut2].reset_index(drop=True)

    # scaler fit on train numeric features only
    num_cols = [c for c in FEATURE_COLS if feat[c].dtype != object]
    scaler = {c: {"mean": float(train[c].mean()), "std": float(train[c].std() or 1.0)}
              for c in num_cols}

    def scaled(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for c in num_cols:
            df[c] = (df[c] - scaler[c]["mean"]) / scaler[c]["std"]
        return df

    feat.to_csv(PROC / "features.csv", index=False)
    train.to_csv(PROC / "train.csv", index=False)
    val.to_csv(PROC / "val.csv", index=False)
    test.to_csv(PROC / "test.csv", index=False)
    scaled(train).to_csv(PROC / "train_scaled.csv", index=False)
    scaled(val).to_csv(PROC / "val_scaled.csv", index=False)
    scaled(test).to_csv(PROC / "test_scaled.csv", index=False)
    (PROC / "split_meta.json").write_text(json.dumps(
        {"cut1": str(pd.Timestamp(cut1).date()), "cut2": str(pd.Timestamp(cut2).date()),
         "n_dates": n, "dropped_window_rows": int(n0 - len(feat)),
         "train": len(train), "val": len(val), "test": len(test),
         "features": FEATURE_COLS, "targets": TARGETS}, indent=2))
    (PROC / "scaler.json").write_text(json.dumps(scaler, indent=2))

    # EDA sanity checks
    corr = feat[["demand_ml", "population", "density", "available_water_ml",
                 "storage_pct", "lag_1", "lag_7", "roll_7", "roll_30"]].corr(
                     numeric_only=True)["demand_ml"].round(3).to_dict()
    seasonal = feat.groupby("season")["demand_ml"].mean().round(3).to_dict()
    per_ward = feat.groupby("ward_id")["demand_ml"].agg(["mean", "std"]).round(3).to_dict()
    report = (
        "# EDA report — Phase 3 (bmc-v1)\n\n"
        f"- rows: full {len(feat)} (dropped {n0 - len(feat)} warmup/tail) | "
        f"train {len(train)} / val {len(val)} / test {len(test)}\n"
        f"- splits: train < {pd.Timestamp(cut1).date()} <= val < {pd.Timestamp(cut2).date()} <= test\n"
        "- leakage: all lags/rolls shift(1)+ per ward; spot-check PASS; targets are future shifts\n"
        f"- corr w/ demand: {corr}\n"
        f"- seasonal mean demand ML: {seasonal}\n"
        f"- per-ward demand stats: {per_ward}\n"
        "- PDF §8 checklist: population/density/growth ✓ lag1/lag7/roll7/roll30/prev-month(lag30) ✓ "
        "reservoir level/storage/pct/avail ✓ month/day/dow/year/season/weekend ✓\n"
    )
    (ROOT / "data" / "eda_report.md").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
