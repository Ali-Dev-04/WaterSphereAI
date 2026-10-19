"""Seed Postgres from data/raw/ CSVs (bmc-v1) + dev users. Idempotent (upserts)."""

import csv
import datetime as dt
import os
from pathlib import Path

from app import models
from app.auth import hash_password
from app.database import SessionLocal

RAW = Path(os.environ.get(
    "SEED_RAW_DIR",
    str(Path(__file__).resolve().parents[1] / "data" / "raw"),
))


def upsert_wards(db, path):
    with open(path) as f:
        for r in csv.DictReader(f):
            db.merge(models.Ward(ward_id=r["ward_id"], ward_name=r["ward_name"],
                                 area_km2=float(r["area_km2"])))


def load_population(db, path):
    with open(path) as f:
        for r in csv.DictReader(f):
            db.merge(models.Population(ward_id=r["ward_id"], year=int(r["year"]),
                                       population=int(r["population"]),
                                       density=float(r["density"]),
                                       growth_pct=float(r["growth_pct"])))


def load_consumption(db, path):
    with open(path) as f:
        for r in csv.DictReader(f):
            d = dt.date.fromisoformat(r["date"])
            db.merge(models.Consumption(ward_id=r["ward_id"], date=d,
                                        demand_ml=float(r["demand_ml"]),
                                        water_supplied_ml=float(r["water_supplied_ml"]),
                                        water_consumed_ml=float(r["water_consumed_ml"])))


def load_reservoirs(db, path, readings_path):
    with open(path) as f:
        for r in csv.DictReader(f):
            db.merge(models.Reservoir(reservoir_id=r["reservoir_id"],
                                      reservoir_name=r["reservoir_name"],
                                      lat=float(r["lat"]), lon=float(r["lon"]),
                                      capacity_mcm=float(r["capacity_mcm"]),
                                      serving_wards=r["serving_wards"]))
    with open(readings_path) as f:
        for r in csv.DictReader(f):
            db.merge(models.ReservoirReading(
                reservoir_id=r["reservoir_id"], date=dt.date.fromisoformat(r["date"]),
                level_m=float(r["level_m"]), capacity_mcm=float(r["capacity_mcm"]),
                current_storage_mcm=float(r["current_storage_mcm"]),
                storage_pct=float(r["storage_pct"]),
                available_water_ml=float(r["available_water_ml"])))


def load_maintenance(db, path):
    with open(path) as f:
        for r in csv.DictReader(f):
            if db.query(models.Maintenance).filter_by(incident_id=r["incident_id"]).first():
                continue
            db.add(models.Maintenance(
                incident_id=r["incident_id"], date=dt.date.fromisoformat(r["date"]),
                ward_id=r["ward_id"], incident_type=r["incident_type"], cause=r["cause"],
                severity=r["severity"],
                resolved_date=dt.date.fromisoformat(r["resolved_date"])))


def seed_users(db):
    admin_u, admin_p = os.environ.get("ADMIN_USER", "admin"), os.environ.get("ADMIN_PASS", "admin123")
    if not db.query(models.User).filter_by(username=admin_u).first():
        db.add(models.User(username=admin_u, password_hash=hash_password(admin_p),
                           role="admin"))
    if not db.query(models.User).filter_by(username="citizen_w1").first():
        db.add(models.User(username="citizen_w1", password_hash=hash_password("citizen123"),
                           role="citizen", ward_id="A"))


def main():
    db = SessionLocal()
    upsert_wards(db, RAW / "wards.csv")
    db.commit()
    load_population(db, RAW / "population.csv")
    load_consumption(db, RAW / "consumption.csv")
    load_reservoirs(db, RAW / "reservoirs.csv", RAW / "reservoir_readings.csv")
    load_maintenance(db, RAW / "maintenance.csv")
    seed_users(db)
    db.commit()
    print("seed ok:",
          db.query(models.Ward).count(), "wards,",
          db.query(models.Consumption).count(), "consumption rows,",
          db.query(models.ReservoirReading).count(), "readings,",
          db.query(models.User).count(), "users")


if __name__ == "__main__":
    main()
