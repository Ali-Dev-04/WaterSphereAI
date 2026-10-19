"""Water-stress endpoint. Citizens confined to their own ward."""

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import stress
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(tags=["stress"])


@router.get("/api/water-stress")
def water_stress(ward_id: str, date: dt.date,
                 horizon: str = Query(default="1d", pattern="^(1d|3d|7d)$"),
                 user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "admin" and user.ward_id != ward_id:
        raise HTTPException(403, "citizens may only view their own ward")
    return stress.compute(db, ward_id, date, horizon)
