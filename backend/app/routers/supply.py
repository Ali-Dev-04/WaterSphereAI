"""Supply-plan endpoint. Citizens see their own ward row only."""

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import planner
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(tags=["supply"])


@router.get("/api/supply-plan")
def supply_plan(date: dt.date, horizon: str = Query(default="1d", pattern="^(1d|3d|7d)$"),
                reserve_pct: float = Query(default=None),
                user=Depends(get_current_user), db: Session = Depends(get_db)):
    plan = planner.plan_for_date(db, date, horizon, reserve_pct)
    if user.role != "admin":
        plan["wards"] = [w for w in plan["wards"] if w["ward_id"] == user.ward_id]
        if not plan["wards"]:
            raise HTTPException(404, "no plan for your ward on this date")
        plan["total_allocated_ml"] = round(sum(w["allocated_ml"] for w in plan["wards"]), 4)
    return plan
