"""GIS endpoint: ward polygons enriched with live stress + reservoir markers."""

import datetime as dt
import json
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, stress
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(tags=["gis"])
GEOJSON_PATH = Path(os.environ.get("WS_BASE", "/code")) / "data" / "raw" / "wards.geojson"


@router.get("/api/gis")
def gis(date: dt.date, user=Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    try:
        fc = json.loads(GEOJSON_PATH.read_text())
    except FileNotFoundError:
        raise HTTPException(500, "ward boundaries unavailable")
    for feat in fc.get("features", []):
        wid = feat["properties"].get("ward_id")
        ward = db.query(models.Ward).filter_by(ward_id=wid).first()
        s = stress.compute(db, wid, date, "1d")
        feat["properties"].update({
            "name": ward.ward_name if ward else wid,
            "forecast_ml": s["forecast_ml"], "available_ml": s["available_ml"],
            "gap_ml": s["gap_ml"], "war": s["war"], "category": s["category"],
        })
    markers = []
    for r in db.query(models.Reservoir).all():
        rd = db.query(models.ReservoirReading).filter_by(
            reservoir_id=r.reservoir_id, date=date).first()
        markers.append({"reservoir_id": r.reservoir_id, "name": r.reservoir_name,
                        "lat": r.lat, "lon": r.lon,
                        "storage_pct": rd.storage_pct if rd else None,
                        "available_ml": rd.available_water_ml if rd else None})
    return {"date": date.isoformat(), "wards": fc, "reservoirs": markers}
