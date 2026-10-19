"""Forecast endpoint: runs the active model per horizon, persists the result."""

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.inference import predict

router = APIRouter(tags=["forecast"])


@router.get("/api/forecast", response_model=schemas.ForecastOut)
def forecast(ward_id: str, target_date: dt.date,
             horizon: str = Query(pattern="^(1d|3d|7d)$"),
             user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "admin" and user.ward_id != ward_id:
        raise HTTPException(403, "citizens may only forecast their own ward")
    value, fam = predict(db, ward_id, target_date, horizon)
    row = db.query(models.Forecast).filter_by(
        ward_id=ward_id, target_date=target_date, horizon=horizon
    ).order_by(models.Forecast.id.desc()).first()
    return schemas.ForecastOut(ward_id=ward_id, target_date=target_date, horizon=horizon,
                               predicted_ml=value, model=fam,
                               model_version=row.model_version if row else "synthetic-v1")
