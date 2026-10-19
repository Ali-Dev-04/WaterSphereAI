"""Model-inference service. Models load once (xgb at startup, keras lazily).

Feature parity with training is critical: tabular order = FEATURE_COLS +
[season_Monsoon, season_PostMonsoon, season_Summer, season_Winter];
sequences = 30-day windows standardized with train stats. Any drift here
invalidates the Phase 5 comparison table.
"""

import datetime as dt
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import models

BASE = Path(os.environ.get("WS_BASE", "/code"))
TAB_FEATURES = [
    "population", "density", "growth_pct", "lag_1", "lag_7", "lag_30",
    "roll_7", "roll_30", "available_water_ml", "storage_pct",
    "day", "day_of_week", "month", "year", "weekend",
    "season_Monsoon", "season_PostMonsoon", "season_Summer", "season_Winter",
]
SEASONS = ["Winter", "Winter", "Summer", "Summer", "Summer", "Summer",
           "Monsoon", "Monsoon", "Monsoon", "PostMonsoon", "PostMonsoon", "Winter"]
H_DAYS = {"1d": 1, "3d": 3, "7d": 7}
MODEL_VERSION = "bmc-v1"

_xgb: dict[str, object] = {}
_keras: dict[str, object] = {}
_scaler: dict = {}
_active: dict[str, str] = {}
_dmean = _dstd = 0.0


def startup() -> None:
    global _scaler, _active, _dmean, _dstd
    _active.update(json.loads((BASE / "models" / "active.json").read_text())["best_per_horizon"])
    _scaler.update(json.loads((BASE / "data" / "processed" / "scaler.json").read_text()))
    tr = pd.read_csv(BASE / "data" / "processed" / "train.csv", usecols=["demand_ml"])
    _dmean, _dstd = float(tr.demand_ml.mean()), float(tr.demand_ml.std())
    for h, fam in _active.items():
        if fam == "xgboost":
            _xgb[h] = joblib.load(BASE / "models" / f"xgb_{h}.pkl")


def _keras_model(h: str):
    import tensorflow as tf  # deferred: TF import costs ~30s, only needed for 7d

    if h not in _keras:
        fam = _active[h]
        _keras[h] = tf.keras.models.load_model(BASE / "models" / f"{fam}_{h}.keras")
    return _keras[h]


def ward_availability(db: Session, ward_id: str, d: dt.date) -> tuple[float, float]:
    res = db.query(models.Reservoir).all()
    tot_av, tot_st, n = 0.0, 0.0, 0
    for r in res:
        served = [s.strip() for s in r.serving_wards.split(";")]
        if ward_id not in served:
            continue
        rd = db.query(models.ReservoirReading).filter_by(
            reservoir_id=r.reservoir_id, date=d).first()
        if not rd:
            raise HTTPException(422, f"no reservoir reading for {r.reservoir_id} on {d}")
        tot_av += rd.available_water_ml / len(served)
        tot_st += rd.storage_pct
        n += 1
    if not n:
        raise HTTPException(422, f"ward {ward_id} has no serving reservoir")
    return tot_av, tot_st / n


def _demand_series(db: Session, ward_id: str) -> pd.DataFrame:
    rows = db.query(models.Consumption).filter_by(ward_id=ward_id).order_by(
        models.Consumption.date).all()
    if len(rows) < 31:
        raise HTTPException(422, f"insufficient history for {ward_id}")
    return pd.DataFrame([{"date": r.date, "demand_ml": r.demand_ml} for r in rows])


def tabular_vector(db: Session, ward_id: str, d: dt.date) -> list[float]:
    hist = _demand_series(db, ward_id)
    past = hist[hist.date <= d].sort_values("date").reset_index(drop=True)
    if past.empty:
        raise HTTPException(422, f"no demand data at/before {d} for {ward_id}")
    dem = past.set_index("date").demand_ml
    pos = dem.index.get_loc(d) if d in dem.index else None
    if pos is None:
        raise HTTPException(422, f"no demand row on feature date {d}")
    if pos < 30:
        raise HTTPException(422, "need ≥30 days history before feature date")
    # Training semantics (features.py): lag_k = demand(d-k), rolls strictly before d.
    lag_1, lag_7, lag_30 = dem.iloc[pos - 1], dem.iloc[pos - 7], dem.iloc[pos - 30]
    roll_7 = dem.iloc[pos - 7:pos].mean()
    roll_30 = dem.iloc[pos - 30:pos].mean()
    pop = db.query(models.Population).filter_by(ward_id=ward_id, year=d.year).first()
    if not pop:
        raise HTTPException(422, f"no population for {ward_id}/{d.year}")
    avail, stor = ward_availability(db, ward_id, d)
    season = SEASONS[d.month - 1]
    dummies = [1.0 if season == s else 0.0
               for s in ("Monsoon", "PostMonsoon", "Summer", "Winter")]
    return [pop.population, pop.density, pop.growth_pct, lag_1, lag_7, lag_30,
            roll_7, roll_30, avail, stor, d.day, d.weekday(), d.month, d.year,
            1.0 if d.weekday() >= 5 else 0.0, *dummies]


def seq_window(db: Session, ward_id: str, d: dt.date) -> np.ndarray:
    hist = _demand_series(db, ward_id)
    past = hist[hist.date <= d].sort_values("date").reset_index(drop=True)
    pos = past.index[past.date == d]
    if not len(pos) or pos[0] < 29:
        raise HTTPException(422, "need ≥30 days history before feature date")
    i = int(pos[0])
    win = past.iloc[i - 29:i + 1].copy()
    avails, stors = [], []
    for r in win.itertuples():
        a, s = ward_availability(db, ward_id, r.date)
        avails.append(a)
        stors.append(s)
    z = lambda v, m, s: (v - m) / s
    mat = np.stack([
        z(win.demand_ml.to_numpy(), _dmean, _dstd),
        z(np.array(avails), _scaler["available_water_ml"]["mean"],
          _scaler["available_water_ml"]["std"]),
        z(np.array(stors), _scaler["storage_pct"]["mean"], _scaler["storage_pct"]["std"]),
        win.date.apply(lambda x: x.weekday() / 6.0).to_numpy(),
        np.sin(2 * np.pi * win.date.apply(lambda x: x.month).to_numpy() / 12),
        np.cos(2 * np.pi * win.date.apply(lambda x: x.month).to_numpy() / 12),
        win.date.apply(lambda x: 1.0 if x.weekday() >= 5 else 0.0).to_numpy(),
    ], axis=1)
    return mat.astype(np.float32)[np.newaxis, :, :]


def predict(db: Session, ward_id: str, target: dt.date, horizon: str) -> tuple[float, str]:
    if horizon not in H_DAYS or horizon not in _active:
        raise HTTPException(422, "horizon must be one of 1d, 3d, 7d")
    if not db.query(models.Ward).filter_by(ward_id=ward_id).first():
        raise HTTPException(404, f"unknown ward {ward_id}")
    fam = _active[horizon]
    d = target - dt.timedelta(days=H_DAYS[horizon])
    if fam == "xgboost":
        vec = np.array(tabular_vector(db, ward_id, d), dtype=float)[np.newaxis, :]
        pred = float(_xgb[horizon].predict(vec)[0])
    else:
        seq = seq_window(db, ward_id, d)
        pred_z = float(_keras_model(horizon).predict(seq, verbose=0).ravel()[0])
        pred = pred_z * _dstd + _dmean
    row = models.Forecast(ward_id=ward_id, target_date=target, horizon=horizon,
                          predicted_ml=round(pred, 4), model=fam, model_version=MODEL_VERSION)
    db.add(row)
    db.commit()
    return round(pred, 4), fam
