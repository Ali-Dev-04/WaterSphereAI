"""Read endpoints for core datasets. Citizens see their own ward only."""

import datetime as dt
import json
import os
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.auth import get_current_user, ward_scope
from app.config import settings
from app.database import get_db

router = APIRouter(tags=["data"])


@router.get("/api/population")
def population(ward_id: str | None = None, year: int | None = None,
               user=Depends(get_current_user), db: Session = Depends(get_db)):
    ward_id = ward_scope(user, ward_id)
    q = db.query(models.Population)
    if ward_id:
        q = q.filter_by(ward_id=ward_id)
    if year:
        q = q.filter_by(year=year)
    q = q.limit(5000)
    return [{"ward_id": r.ward_id, "year": r.year, "population": r.population,
             "density": r.density, "growth_pct": r.growth_pct} for r in q.all()]


@router.get("/api/consumption")
def consumption(ward_id: str | None = None, date_from: dt.date | None = None,
                date_to: dt.date | None = None,
                user=Depends(get_current_user), db: Session = Depends(get_db)):
    ward_id = ward_scope(user, ward_id)
    q = db.query(models.Consumption).order_by(models.Consumption.date)
    if ward_id:
        q = q.filter_by(ward_id=ward_id)
    if date_from:
        q = q.filter(models.Consumption.date >= date_from)
    if date_to:
        q = q.filter(models.Consumption.date <= date_to)
    rows = q.limit(5000).all()
    return [{"ward_id": r.ward_id, "date": r.date.isoformat(), "demand_ml": r.demand_ml,
             "supplied_ml": r.water_supplied_ml, "consumed_ml": r.water_consumed_ml}
            for r in rows]


@router.get("/api/reservoir")
def reservoir(reservoir_id: str | None = None, date_from: dt.date | None = None,
              date_to: dt.date | None = None,
              user=Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    out = []
    q = db.query(models.Reservoir)
    if reservoir_id:
        q = q.filter_by(reservoir_id=reservoir_id)
    for r in q.all():
        rq = db.query(models.ReservoirReading).filter_by(
            reservoir_id=r.reservoir_id).order_by(models.ReservoirReading.date)
        if date_from:
            rq = rq.filter(models.ReservoirReading.date >= date_from)
        if date_to:
            rq = rq.filter(models.ReservoirReading.date <= date_to)
        readings = rq.limit(5000).all()
        out.append({"reservoir_id": r.reservoir_id, "name": r.reservoir_name,
                    "capacity_mcm": r.capacity_mcm, "serving_wards": r.serving_wards,
                    "readings": [{"date": x.date.isoformat(),
                                  "storage_pct": x.storage_pct,
                                  "available_ml": x.available_water_ml} for x in readings]})
    return out


@router.get("/api/wards")
def wards(user=Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    return [{"ward_id": w.ward_id, "name": w.ward_name, "area_km2": w.area_km2}
            for w in db.query(models.Ward).all()]


@router.get("/api/public/wards")
def public_wards(db: Session = Depends(get_db)):
    """Unauthenticated ward list for the citizen sign-up form (public municipal info)."""
    return [{"ward_id": w.ward_id, "name": w.ward_name, "area_km2": w.area_km2}
            for w in db.query(models.Ward).order_by(models.Ward.ward_id).all()]


MODELS_DIR = Path(os.environ.get("WS_BASE", "/code")) / "models"


def _registry_version() -> str:
    """Model version from the registry manifest; config fallback if artifacts absent."""
    try:
        return json.loads((MODELS_DIR / "manifest.json").read_text())["model_version"]
    except Exception:
        return settings.model_version


@router.get("/api/meta")
def meta(db: Session = Depends(get_db)):
    """Public display configuration — drives UI copy so nothing is hardcoded.

    Deliberately exposes only non-sensitive values: ward count, dataset window,
    WAR bands and the model version. No credentials, paths or internals.
    """
    dmin, dmax = db.query(func.min(models.Consumption.date),
                          func.max(models.Consumption.date)).one()
    return {
        "model_version": _registry_version(),
        "ward_count": db.query(models.Ward).count(),
        "window": {"min_date": (dmin or dt.date.today()).isoformat(),
                   "max_date": (dmax or dt.date.today()).isoformat()},
        "war": {"safe": settings.war_safe,
                "moderate": settings.war_moderate,
                "high": settings.war_high},
    }


@router.get("/api/model-info")
def model_info(user=Depends(get_current_user)):
    """Active model per horizon + its held-out test scores (from the registry).

    Lets the dashboard label forecasts with measured accuracy instead of
    hardcoded constants. Refresh strategy: re-run train → evaluate → registry.
    """
    _ = user
    active = json.loads((MODELS_DIR / "active.json").read_text())
    return {"model_version": _registry_version(),
            "selected_on": active["selected_on"],
            "active_per_horizon": active["best_per_horizon"],
            "test_scores": active["test_scores_of_selected"]}
