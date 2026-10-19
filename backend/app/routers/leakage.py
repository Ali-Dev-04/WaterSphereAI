"""Leakage-risk + maintenance reads. Citizens confined to their own ward."""

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import leakage, models
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(tags=["leakage"])


@router.get("/api/leakage-risk")
def leakage_risk(ward_id: str, date_from: dt.date, date_to: dt.date,
                 user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "admin" and user.ward_id != ward_id:
        raise HTTPException(403, "citizens may only view their own ward")
    return leakage.ward_report(db, ward_id, date_from, date_to)


@router.get("/api/maintenance")
def maintenance(ward_id: str | None = Query(default=None),
                user=Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    q = db.query(models.Maintenance).order_by(models.Maintenance.date.desc())
    if ward_id:
        q = q.filter_by(ward_id=ward_id)
    return [{"incident_id": m.incident_id, "date": m.date.isoformat(),
             "ward_id": m.ward_id, "type": m.incident_type, "cause": m.cause,
             "severity": m.severity,
             "resolved": m.resolved_date.isoformat() if m.resolved_date else None}
            for m in q.limit(200).all()]
