"""Phase 4: train baselines + XGBoost/LSTM/GRU/Transformer per horizon (1/3/7-day).

Tuning on validation only; test set untouched (Phase 5). Fixed seeds throughout.
Tabular (XGBoost): FEATURE_COLS + season dummies from train_scaled-equivalent.
Sequential (DL): 30-day windows of [demand_z, avail_z, storage_z, dow, sin/cos month,
weekend] built per ward from merged timeline; targets standardized, inverted at eval.
Saves models/*.pkl/*.keras + data/validation_metrics.json
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
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
try:
    from xgboost import XGBRegressor
    def get_xgboost_model(seed):
        return XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05,
                            subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                            random_state=seed, n_jobs=-1, tree_method="hist")
except Exception:
    from sklearn.ensemble import HistGradientBoostingRegressor
    def get_xgboost_model(seed):
        return HistGradientBoostingRegressor(max_iter=300, max_depth=6, learning_rate=0.05,
                                              l2_regularization=1.0, random_state=seed)

import tensorflow as tf

SEED = 42
WINDOW = 30
HORIZONS = {"1d": ("target_1d", 1), "3d": ("target_3d", 3), "7d": ("target_7d", 7)}
FEATURE_COLS = [
    "population", "density", "growth_pct", "lag_1", "lag_7", "lag_30",
    "roll_7", "roll_30", "available_water_ml", "storage_pct",
    "day", "day_of_week", "month", "year", "weekend",
]

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
MODELS = ROOT / "models"

np.random.seed(SEED)
tf.keras.utils.set_random_seed(SEED)
try:
    tf.config.experimental.enable_op_determinism()
except Exception:  # CPU-only builds vary; seeds still fixed
    pass


def mape(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean(np.abs((y - p) / np.maximum(y, 1e-9))) * 100)


def scores(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y, p)),
        "rmse": float(mean_squared_error(y, p) ** 0.5),
        "mape": mape(y, p),
        "r2": float(r2_score(y, p)),
    }


def build_lstm(dim: int) -> tf.keras.Model:
    m = tf.keras.Sequential(
        [tf.keras.layers.Input((WINDOW, dim)), tf.keras.layers.LSTM(32),
         tf.keras.layers.Dense(16, activation="relu"), tf.keras.layers.Dense(1)]
    )
    m.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="mse")
    return m


def build_gru(dim: int) -> tf.keras.Model:
    m = tf.keras.Sequential(
        [tf.keras.layers.Input((WINDOW, dim)), tf.keras.layers.GRU(32),
         tf.keras.layers.Dense(16, activation="relu"), tf.keras.layers.Dense(1)]
    )
    m.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="mse")
    return m


def build_transformer(dim: int) -> tf.keras.Model:
    x_in = tf.keras.layers.Input((WINDOW, dim))
    x = tf.keras.layers.Dense(32)(x_in)
    for _ in range(2):
        a = tf.keras.layers.MultiHeadAttention(num_heads=2, key_dim=16)(x, x)
        x = tf.keras.layers.LayerNormalization()(x + a)
        f = tf.keras.layers.Dense(64, activation="relu")(x)
        f = tf.keras.layers.Dense(32)(f)
        x = tf.keras.layers.LayerNormalization()(x + f)
    x = tf.keras.layers.GlobalAveragePooling1D()(x)
    x = tf.keras.layers.Dense(16, activation="relu")(x)
    out = tf.keras.layers.Dense(1)(x)
    m = tf.keras.Model(x_in, out)
    m.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="mse")
    return m


def seq_dataset(feat_full: pd.DataFrame, ward: str, h: int, dmean: float, dstd: float,
                avail_mean: float, avail_std: float, stor_mean: float, stor_std: float,
                cut1: str, cut2: str, split: str) -> tuple[np.ndarray, np.ndarray]:
    sub = feat_full[feat_full.ward_id == ward].sort_values("date").reset_index(drop=True)
    dem = sub.demand_ml.to_numpy()
    av = sub.available_water_ml.to_numpy()
    st = sub.storage_pct.to_numpy()
    dates = sub.date.dt.strftime("%Y-%m-%d").to_numpy()
    dow = sub.day_of_week.to_numpy() / 6.0
    mon = sub.month.to_numpy()
    sin_c, cos_c = np.sin(2 * np.pi * mon / 12), np.cos(2 * np.pi * mon / 12)
    wk = sub.weekend.to_numpy().astype(float)
    z = lambda v, m, s: (v - m) / s
    mat = np.stack([z(dem, dmean, dstd), z(av, avail_mean, avail_std), z(st, stor_mean, stor_std),
                    dow, sin_c, cos_c, wk], axis=1)
    n = len(sub)
    xs, ys, ds = [], [], []
    for i in range(WINDOW, n - h + 1):
        xs.append(mat[i - WINDOW:i])
        ys.append((dem[i + h - 1] - dmean) / dstd)
        ds.append(dates[i + h - 1])
    xs = np.array(xs, dtype=np.float32)
    ys = np.array(ys, dtype=np.float32)
    ds = np.array(ds)
    if split == "train":
        keep = ds < cut1
    elif split == "val":
        keep = (ds >= cut1) & (ds < cut2)
    else:
        keep = ds >= cut2
    return xs[keep], ys[keep]


def main() -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    train = pd.read_csv(PROC / "train.csv", parse_dates=["date"])
    val = pd.read_csv(PROC / "val.csv", parse_dates=["date"])
    meta = json.loads((PROC / "split_meta.json").read_text())
    cut1, cut2 = meta["cut1"], meta["cut2"]
    tab_feats = FEATURE_COLS + [c for c in train.columns if c.startswith("season_")]

    Xtr, Xva = train[tab_feats].to_numpy(), val[tab_feats].to_numpy()
    metrics: dict[str, dict[str, dict[str, float]]] = {}

    # ---- baselines from demand series (val only) ----
    for hname, (_, h) in HORIZONS.items():
        y = val[f"target_{hname}"].to_numpy()
        naive = val["demand_ml"].to_numpy()  # persist last observed
        # seasonal-naive: demand 7 days before target = demand at (t+h-7); reconstruct per ward
        seas_pred = []
        for _, g in val.sort_values(["ward_id", "date"]).groupby("ward_id"):
            d = g.demand_ml.to_numpy()
            # target index i corresponds to demand at t+h; seasonal ref is value 7d earlier
            # approximate with lag chain: ref = demand shifted by (7-h) within val, backfilled from train tail
            w = g.ward_id.iloc[0]
            full = pd.concat([train[train.ward_id == w].sort_values("date"),
                              g]).reset_index(drop=True)
            ref = full.demand_ml.shift(7).iloc[len(full) - len(g):].to_numpy()
            seas_pred.extend(ref.tolist())
        seas_pred = np.array(seas_pred)
        metrics.setdefault("naive", {})[hname] = scores(y, naive)
        metrics.setdefault("seasonal_naive", {})[hname] = scores(y, seas_pred)

    # ---- XGBoost per horizon ----
    for hname, (tcol, _) in HORIZONS.items():
        ytr, yva = train[tcol].to_numpy(), val[tcol].to_numpy()
        reg = get_xgboost_model(SEED)
        reg.fit(Xtr, ytr)
        joblib.dump(reg, MODELS / f"xgb_{hname}.pkl")
        metrics.setdefault("xgboost", {})[hname] = scores(yva, reg.predict(Xva))

    # ---- DL sequences ----
    merged = pd.read_csv(PROC / "merged_ward_date.csv", parse_dates=["date"])
    scaler = json.loads((PROC / "scaler.json").read_text())
    dmean, dstd = float(train.demand_ml.mean()), float(train.demand_ml.std())
    am, as_ = scaler["available_water_ml"]["mean"], scaler["available_water_ml"]["std"]
    sm, ss = scaler["storage_pct"]["mean"], scaler["storage_pct"]["std"]
    wards = sorted(merged.ward_id.unique())
    builders = {"lstm": build_lstm, "gru": build_gru, "transformer": build_transformer}
    cb = [tf.keras.callbacks.EarlyStopping(patience=8, restore_best_weights=True, monitor="val_loss")]

    for arch, build in builders.items():
        for hname, (_, h) in HORIZONS.items():
            Xt_list, yt_list, Xv_list, yv_list = [], [], [], []
            for w in wards:
                xtr, ytr = seq_dataset(merged, w, h, dmean, dstd, am, as_, sm, ss, cut1, cut2, "train")
                xva, yva = seq_dataset(merged, w, h, dmean, dstd, am, as_, sm, ss, cut1, cut2, "val")
                Xt_list.append(xtr)
                yt_list.append(ytr)
                Xv_list.append(xva)
                yv_list.append(yva)
            Xt, yt = np.concatenate(Xt_list), np.concatenate(yt_list)
            Xv, yv = np.concatenate(Xv_list), np.concatenate(yv_list)
            model = build(Xt.shape[2])
            model.fit(Xt, yt, validation_data=(Xv, yv), epochs=60, batch_size=64,
                      callbacks=cb, verbose=0)
            model.save(MODELS / f"{arch}_{hname}.keras")
            pred_z = model.predict(Xv, verbose=0).ravel()
            pred = pred_z * dstd + dmean
            yv_raw = yv * dstd + dmean
            metrics.setdefault(arch, {})[hname] = scores(yv_raw, pred)
            print(f"{arch} {hname}: val MAE={metrics[arch][hname]['mae']:.4f} "
                  f"RMSE={metrics[arch][hname]['rmse']:.4f}", flush=True)

    (ROOT / "data" / "validation_metrics.json").write_text(json.dumps(metrics, indent=2))
    print("\n== validation MAE (lower better) ==")
    fams = ["naive", "seasonal_naive", "xgboost", "lstm", "gru", "transformer"]
    print("family | " + " | ".join(HORIZONS))
    for f in fams:
        print(f"{f:15s} | " + " | ".join(f"{metrics[f][h]['mae']:.4f}" for h in HORIZONS))


if __name__ == "__main__":
    main()
