"""PostgreSQL schema. Table/column names match Architecture.md §4 (snake_case)."""

import datetime as dt

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(16), default="citizen")  # admin | citizen
    ward_id: Mapped[str | None] = mapped_column(String(16), ForeignKey("wards.ward_id"))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class Ward(Base):
    __tablename__ = "wards"
    ward_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    ward_name: Mapped[str] = mapped_column(String(64))
    area_km2: Mapped[float] = mapped_column(Float)


class Population(Base):
    __tablename__ = "population"
    ward_id: Mapped[str] = mapped_column(String(16), ForeignKey("wards.ward_id"), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    population: Mapped[int] = mapped_column(Integer)
    density: Mapped[float] = mapped_column(Float)
    growth_pct: Mapped[float] = mapped_column(Float)


class Consumption(Base):
    __tablename__ = "consumption"
    ward_id: Mapped[str] = mapped_column(String(16), ForeignKey("wards.ward_id"), primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    demand_ml: Mapped[float] = mapped_column(Float)
    water_supplied_ml: Mapped[float] = mapped_column(Float)
    water_consumed_ml: Mapped[float] = mapped_column(Float)


class Reservoir(Base):
    __tablename__ = "reservoirs"
    reservoir_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    reservoir_name: Mapped[str] = mapped_column(String(64))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    capacity_mcm: Mapped[float] = mapped_column(Float)
    serving_wards: Mapped[str] = mapped_column(Text)  # semicolon-separated ward_ids


class ReservoirReading(Base):
    __tablename__ = "reservoir_readings"
    reservoir_id: Mapped[str] = mapped_column(
        String(16), ForeignKey("reservoirs.reservoir_id"), primary_key=True
    )
    date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    level_m: Mapped[float] = mapped_column(Float)
    capacity_mcm: Mapped[float] = mapped_column(Float)
    current_storage_mcm: Mapped[float] = mapped_column(Float)
    storage_pct: Mapped[float] = mapped_column(Float)
    available_water_ml: Mapped[float] = mapped_column(Float)


class Forecast(Base):
    __tablename__ = "forecasts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ward_id: Mapped[str] = mapped_column(String(16), ForeignKey("wards.ward_id"), index=True)
    target_date: Mapped[dt.date] = mapped_column(Date, index=True)
    horizon: Mapped[str] = mapped_column(String(8))  # 1d | 3d | 7d
    predicted_ml: Mapped[float] = mapped_column(Float)
    model: Mapped[str] = mapped_column(String(32))
    model_version: Mapped[str] = mapped_column(String(32), default="synthetic-v1")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class WaterStress(Base):
    """Filled by Phase 7 engine. Table created now so migrations stay linear."""

    __tablename__ = "water_stress"
    ward_id: Mapped[str] = mapped_column(String(16), ForeignKey("wards.ward_id"), primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    gap_ml: Mapped[float] = mapped_column(Float)
    war: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(16))


class SupplyPlan(Base):
    """Filled by Phase 8 engine."""

    __tablename__ = "supply_plans"
    ward_id: Mapped[str] = mapped_column(String(16), ForeignKey("wards.ward_id"), primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    allocated_ml: Mapped[float] = mapped_column(Float)
    alert: Mapped[bool] = mapped_column(default=False)


class Complaint(Base):
    __tablename__ = "complaints"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    ward_id: Mapped[str] = mapped_column(String(16), ForeignKey("wards.ward_id"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="Filed")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow
    )


class Maintenance(Base):
    __tablename__ = "maintenance"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(16), unique=True)
    date: Mapped[dt.date] = mapped_column(Date)
    ward_id: Mapped[str] = mapped_column(String(16), ForeignKey("wards.ward_id"), index=True)
    incident_type: Mapped[str] = mapped_column(String(32))
    cause: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(16))
    resolved_date: Mapped[dt.date | None] = mapped_column(Date)
