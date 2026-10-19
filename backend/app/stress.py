"""Water-stress engine (Phase 7). Pure logic + DB persistence.

Canonical formulas:
  gap = forecasted_demand - available_water
  war = available_water / forecasted_demand   (guarded: forecast <= 0 → Shortage)
Thresholds come from Settings (env-overridable), never hardcoded.
"""

import datetime as dt

from sqlalchemy.orm import Session

from app import inference, models
from app.config import settings


def classify(war: float) -> str:
    if war >= settings.war_safe:
        return "Safe"
    if war >= settings.war_moderate:
        return "Moderate"
    if war >= settings.war_high:
        return "High Stress"
    return "Shortage"


def compute(db: Session, ward_id: str, date: dt.date,
            horizon: str = "1d") -> dict:
    predicted, model = inference.predict(db, ward_id, date, horizon)
    available, _ = inference.ward_availability(db, ward_id, date)
    gap = round(predicted - available, 4)
    war = round(available / predicted, 4) if predicted > 0 else 0.0
    category = classify(war) if predicted > 0 else "Shortage"
    if horizon == "1d":
        db.merge(models.WaterStress(ward_id=ward_id, date=date, gap_ml=gap,
                                    war=war, category=category))
        db.commit()
    return {"ward_id": ward_id, "date": date.isoformat(), "horizon": horizon,
            "forecast_ml": predicted, "forecast_model": model,
            "available_ml": round(available, 4), "gap_ml": gap,
            "war": war, "category": category}
