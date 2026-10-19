"""Resume BMC retrain after interruption: xgb/lstm/gru artifacts are fresh.

Recomputes validation scores for the already-trained families by inference
(no retraining), trains ONLY the transformer family (missing), and writes
data/validation_metrics.json. Run: python3 scripts/resume_transformers.py
Then: python3 scripts/evaluate.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ["KERAS_HOME"] = str(ROOT / ".keras")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
sys.path.insert(0, str(ROOT / "scripts"))

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf

from train import HORIZONS, FEATURE_COLS, scores, seq_dataset, build_transformer

PROC = ROOT / "data" / "processed"
MODELS = ROOT / "models"

tf.keras.utils.set_random_seed(42)


def main() -> None:
    train = pd.read_csv(PROC / "train.csv", parse_dates=["date"])
    val = pd.read_csv(PROC / "val.csv", parse_dates=["date"])
    meta = json.loads((PROC / "split_meta.json").read_text())
    cut1, cut2 = meta["cut1"], meta["cut2"]
    tab_feats = FEATURE_COLS + [c for c in train.columns if c.startswith("season_")]
    Xva = val[tab_feats].to_numpy()
    metrics: dict[str, dict[str, dict[str, float]]] = {}

    for hname, (_, h) in HORIZONS.items():
        y = val[f"target_{hname}"].to_numpy()
        metrics.setdefault("naive", {})[hname] = scores(y, val["demand_ml"].to_numpy())
        seas_pred = []
        for _, g in val.sort_values(["ward_id", "date"]).groupby("ward_id"):
            w = g.ward_id.iloc[0]
            full = pd.concat([train[train.ward_id == w].sort_values("date"),
                              g]).reset_index(drop=True)
            ref = full.demand_ml.shift(7).iloc[len(full) - len(g):].to_numpy()
            seas_pred.extend(ref.tolist())
        metrics.setdefault("seasonal_naive", {})[hname] = scores(y, np.array(seas_pred))

    for hname in HORIZONS:
        reg = joblib.load(MODELS / f"xgb_{hname}.pkl")
        yva = val[f"target_{hname}"].to_numpy()
        metrics.setdefault("xgboost", {})[hname] = scores(yva, reg.predict(Xva))
        print(f"xgboost {hname}: val MAE={metrics['xgboost'][hname]['mae']:.4f}", flush=True)

    merged = pd.read_csv(PROC / "merged_ward_date.csv", parse_dates=["date"])
    scaler = json.loads((PROC / "scaler.json").read_text())
    dmean, dstd = float(train.demand_ml.mean()), float(train.demand_ml.std())
    am, as_ = scaler["available_water_ml"]["mean"], scaler["available_water_ml"]["std"]
    sm, ss = scaler["storage_pct"]["mean"], scaler["storage_pct"]["std"]
    wards = sorted(merged.ward_id.unique())
    cb = [tf.keras.callbacks.EarlyStopping(patience=8, restore_best_weights=True,
                                           monitor="val_loss")]

    for arch in ("lstm", "gru"):
        for hname, (_, h) in HORIZONS.items():
            Xv_list, yv_list = [], []
            for w in wards:
                xva, yva = seq_dataset(merged, w, h, dmean, dstd, am, as_, sm, ss,
                                       cut1, cut2, "val")
                Xv_list.append(xva)
                yv_list.append(yva)
            Xv = np.concatenate(Xv_list)
            yv_raw = np.concatenate(yv_list) * dstd + dmean
            model = tf.keras.models.load_model(MODELS / f"{arch}_{hname}.keras")
            pred = model.predict(Xv, verbose=0).ravel() * dstd + dmean
            metrics.setdefault(arch, {})[hname] = scores(yv_raw, pred)
            print(f"{arch} {hname}: val MAE={metrics[arch][hname]['mae']:.4f}", flush=True)

    for hname, (_, h) in HORIZONS.items():
        Xt_list, yt_list, Xv_list, yv_list = [], [], [], []
        for w in wards:
            xtr, ytr = seq_dataset(merged, w, h, dmean, dstd, am, as_, sm, ss,
                                   cut1, cut2, "train")
            xva, yva = seq_dataset(merged, w, h, dmean, dstd, am, as_, sm, ss,
                                   cut1, cut2, "val")
            Xt_list.append(xtr)
            yt_list.append(ytr)
            Xv_list.append(xva)
            yv_list.append(yva)
        Xt, yt = np.concatenate(Xt_list), np.concatenate(yt_list)
        Xv, yv = np.concatenate(Xv_list), np.concatenate(yv_list)
        model = build_transformer(Xt.shape[2])
        model.fit(Xt, yt, validation_data=(Xv, yv), epochs=60, batch_size=64,
                  callbacks=cb, verbose=0)
        model.save(MODELS / f"transformer_{hname}.keras")
        pred = model.predict(Xv, verbose=0).ravel() * dstd + dmean
        metrics.setdefault("transformer", {})[hname] = scores(yv * dstd + dmean, pred)
        print(f"transformer {hname}: val MAE={metrics['transformer'][hname]['mae']:.4f}",
              flush=True)

    (ROOT / "data" / "validation_metrics.json").write_text(json.dumps(metrics, indent=2))
    print("\n== validation MAE (lower better) ==")
    for f in ["naive", "seasonal_naive", "xgboost", "lstm", "gru", "transformer"]:
        print(f"{f:15s} | " + " | ".join(f"{metrics[f][h]['mae']:.4f}" for h in HORIZONS))


if __name__ == "__main__":
    main()
