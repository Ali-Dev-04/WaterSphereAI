"""Leakage/wastage supporting module (Phase 12, unsupervised).

Water Loss = supplied - consumed (exact, per reading).
Anomaly flags: IsolationForest per ward over [loss_ml, loss_pct, roll7_loss,
day-over-day consumption change]. Unsupervised by design — the synthetic
maintenance seeds are incident samples, not per-row labels, so supervised
classification stays Future scope per plan until real labels exist.
"""

import datetime as dt

import numpy as np
import pandas as pd
from fastapi import HTTPException
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session

from app import models

CONTAMINATION = 0.05


def loss_frame(dates: list[dt.date], supplied: list[float],
               consumed: list[float]) -> pd.DataFrame:
    df = pd.DataFrame({"date": pd.to_datetime(dates), "supplied": supplied,
                       "consumed": consumed}).sort_values("date").reset_index(drop=True)
    df["loss_ml"] = df.supplied - df.consumed
    df["loss_pct"] = np.where(df.supplied > 0, df.loss_ml / df.supplied, 0.0)
    df["roll7_loss"] = df.loss_ml.rolling(7, min_periods=1).mean()
    df["consumed_chg"] = df.consumed.diff().fillna(0.0)
    return df


def flag_anomalies(df: pd.DataFrame,
                   contamination: float = CONTAMINATION) -> pd.DataFrame:
    feats = df[["loss_ml", "loss_pct", "roll7_loss", "consumed_chg"]].to_numpy()
    clf = IsolationForest(contamination=contamination, random_state=42)
    pred = clf.fit_predict(feats)
    score = clf.decision_function(feats)
    df = df.copy()
    df["flag"] = pred == -1
    df["score"] = np.round(score, 4)
    df["severity"] = np.where(df.flag & (df.score < -0.15), "high",
                              np.where(df.flag, "medium", "none"))
    return df


def ward_report(db: Session, ward_id: str, date_from: dt.date,
                date_to: dt.date) -> dict:
    if not db.query(models.Ward).filter_by(ward_id=ward_id).first():
        raise HTTPException(404, f"unknown ward {ward_id}")
    rows = db.query(models.Consumption).filter_by(ward_id=ward_id).filter(
        models.Consumption.date >= date_from, models.Consumption.date <= date_to
    ).order_by(models.Consumption.date).all()
    if len(rows) < 14:
        raise HTTPException(422, "need ≥14 days in range for anomaly detection")
    df = flag_anomalies(loss_frame([r.date for r in rows],
                                   [r.water_supplied_ml for r in rows],
                                   [r.water_consumed_ml for r in rows]))
    flags = df[df.flag].sort_values("date")
    return {
        "ward_id": ward_id, "from": date_from.isoformat(), "to": date_to.isoformat(),
        "loss_ml_total": round(float(df.loss_ml.sum()), 3),
        "loss_pct_avg": round(float(df.loss_pct.mean() * 100), 2),
        "readings": len(df), "flagged": int(df.flag.sum()),
        "flags": [{"date": r.date.strftime("%Y-%m-%d"), "loss_ml": round(float(r.loss_ml), 3),
                   "loss_pct": round(float(r.loss_pct * 100), 2),
                   "score": float(r.score), "severity": r.severity}
                  for r in flags.itertuples()],
    }
