"""Phase 5: one-time test-set evaluation, comparison table, best-per-horizon selection.

Selection uses VALIDATION RMSE (never test). Test is scored in a single pass.
Reads models/*.pkl/*.keras + data/validation_metrics.json.
Writes data/test_metrics.json, data/comparison_table.md, models/active.json
"""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ["KERAS_HOME"] = str(ROOT / ".keras")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf

from train import HORIZONS, FEATURE_COLS, scores, seq_dataset

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
MODELS = ROOT / "models"


def main() -> None:
    test = pd.read_csv(PROC / "test.csv", parse_dates=["date"])
    train = pd.read_csv(PROC / "train.csv", parse_dates=["date"])
    meta = json.loads((PROC / "split_meta.json").read_text())
    cut1, cut2 = meta["cut1"], meta["cut2"]
    tab_feats = FEATURE_COLS + [c for c in train.columns if c.startswith("season_")]
    Xte = test[tab_feats].to_numpy()

    merged = pd.read_csv(PROC / "merged_ward_date.csv", parse_dates=["date"])
    scaler = json.loads((PROC / "scaler.json").read_text())
    dmean, dstd = float(train.demand_ml.mean()), float(train.demand_ml.std())
    am, as_ = scaler["available_water_ml"]["mean"], scaler["available_water_ml"]["std"]
    sm, ss = scaler["storage_pct"]["mean"], scaler["storage_pct"]["std"]
    wards = sorted(merged.ward_id.unique())

    results: dict[str, dict[str, dict[str, float]]] = {}

    for hname, (tcol, h) in HORIZONS.items():
        y = test[tcol].to_numpy()
        results.setdefault("naive", {})[hname] = scores(y, test.demand_ml.to_numpy())
        seas_pred = []
        for _, g in test.sort_values(["ward_id", "date"]).groupby("ward_id"):
            w = g.ward_id.iloc[0]
            full = pd.concat([train[train.ward_id == w].sort_values("date"),
                              pd.read_csv(PROC / "val.csv", parse_dates=["date"])
                              .query("ward_id == @w").sort_values("date"), g])
            ref = full.demand_ml.shift(7).iloc[len(full) - len(g):].to_numpy()
            seas_pred.extend(ref.tolist())
        results.setdefault("seasonal_naive", {})[hname] = scores(y, np.array(seas_pred))

        reg = joblib.load(MODELS / f"xgb_{hname}.pkl")
        results.setdefault("xgboost", {})[hname] = scores(y, reg.predict(Xte))

        Xt_list, yt_list = [], []
        for w in wards:
            xte, yte = seq_dataset(merged, w, h, dmean, dstd, am, as_, sm, ss,
                                   cut1, cut2, "test")
            Xt_list.append(xte)
            yt_list.append(yte)
        Xte_s = np.concatenate(Xt_list)
        yte_raw = np.concatenate(yt_list) * dstd + dmean
        for arch in ("lstm", "gru", "transformer"):
            model = tf.keras.models.load_model(MODELS / f"{arch}_{hname}.keras")
            pred = model.predict(Xte_s, verbose=0).ravel() * dstd + dmean
            results.setdefault(arch, {})[hname] = scores(yte_raw, pred)

    valm = json.loads((ROOT / "data" / "validation_metrics.json").read_text())
    cands = ["xgboost", "lstm", "gru", "transformer"]
    active = {h: min(cands, key=lambda f: valm[f][h]["rmse"]) for h in HORIZONS}
    (MODELS / "active.json").write_text(json.dumps(
        {"best_per_horizon": active, "selected_on": "validation RMSE",
         "test_scores_of_selected": {h: results[active[h]][h] for h in HORIZONS}}, indent=2))
    (ROOT / "data" / "test_metrics.json").write_text(json.dumps(results, indent=2))

    lines = ["# Model comparison — test set (bmc-v1, single pass)\n",
             f"Selected on validation RMSE → active: {active}\n",
             "| model | " + " | ".join(f"{h} MAE/RMSE/MAPE/R²" for h in HORIZONS) + " |",
             "|---|---|---|---|"]
    for f in ["naive", "seasonal_naive"] + cands:
        cells = " | ".join(
            f"{results[f][h]['mae']:.4f}/{results[f][h]['rmse']:.4f}/"
            f"{results[f][h]['mape']:.2f}%/{results[f][h]['r2']:.4f}" for h in HORIZONS)
        mark = " **← active**" if f in set(active.values()) else ""
        lines.append(f"| {f}{mark} | {cells} |")
    (ROOT / "data" / "comparison_table.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
