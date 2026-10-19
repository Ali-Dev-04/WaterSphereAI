# Architecture.md — WaterSphere AI

## 1. Block Diagram (from Docs/Architecture.jpeg, 11 blocks)
```
[1 DATA SOURCES: Population, Density, Consumption, Reservoir, Time/Season]
  → [PREPROCESSING & FEATURE ENG: clean, missing, outliers, normalize, integrate,
     extract/scale, select, reduce, sample, ward+time align]
  → [2 DATA PREPARATION: train/val/test chronological split, labels=Actual Demand]
  → [3 MODEL TRAINING: XGBoost | LSTM | GRU | Transformer]
  → [4 VALIDATION & SELECTION: CV + tuning, MAE/RMSE/MAPE/R² → best model]
  → [5 EVALUATION: test set, Final Forecasting Model]
  → [6 PREDICTION: 1-day | 3-day | 7-day forecasts]
  → ([7 RESERVOIR AVAILABILITY: level, storage, storage%, available] × [8 DEMAND–SUPPLY: gap])
  → [9 WATER STRESS: Safe | Moderate | High Stress | Shortage (WAR)]
  → [10 SMART SUPPLY PLAN: zone allocation, recommendation, shortage alert]
  → [11 OUTPUTS: Admin Dashboard (React) | GIS (Leaflet+OSM) | Citizen App (Flutter)]
DATABASE (PostgreSQL) underpins 7–11: stores all data, models metadata, forecasts, plans, interactions.
```

## 2. Tech Stack (confirmed unless noted)
| Layer | Choice |
|---|---|
| Languages | Python (ML/backend), JS/TS (dashboard), Dart (app) |
| Data/ML | Pandas, NumPy, Scikit-learn, XGBoost; TF/Keras for LSTM/GRU/Transformer (PyTorch = allowed alternative, record in Context.md if switched) |
| Metrics | MAE, RMSE, MAPE, R² |
| DB | PostgreSQL + SQLAlchemy/SQLModel + Alembic |
| API | FastAPI (routers → services → repository), Pydantic, JWT (`python-jose`, `passlib[bcrypt]`) |
| Dashboard | React + Recharts/Plotly, react-leaflet |
| Mobile | Flutter + FCM |
| Deploy | Render (API+DB), Netlify (dashboard); Docker for parity |

## 3. API Surface
`GET /api/population`, `GET/POST /api/consumption`, `GET /api/reservoir`, `GET /api/forecast?ward&horizon`, `GET /api/water-stress?ward&date`, `GET /api/supply-plan?date`, `GET /api/leakage-risk?ward`, `CRUD /api/complaints`. Auto-generated OpenAPI is the contract. Inference service loads the active model per horizon once at startup (never per request).

## 4. Database (10 tables)
`Users(id, role, ward_id, hash)`, `Wards(id, name, geom_ref, area)`, `Population(ward_id, year, pop, density, growth)`, `Consumption(ward_id, date, consumed, supplied, demand)`, `Reservoir(id, name, lat, lon, capacity)`, `ReservoirReading(reservoir_id, date, level, storage, storage_pct, available)` (or columns on Reservoir per plan §22 — finalize at Phase 6 and record), `Forecast(ward_id, date, horizon, value, model, model_version)`, `WaterStress(ward_id, date, gap, war, category)`, `SupplyPlan(ward_id, date, allocated, alert)`, `Complaints(id, user, ward_id, type, status, timestamps)`, `Maintenance(...)`. Relations: Ward → Population/Consumption/Forecast/WaterStress/SupplyPlan; Reservoir → Readings → WaterStress; Forecast + Availability → Stress → Plan.

## 5. Key Business Logic (canonical)
- `Storage% = Current / Capacity × 100`
- `Gap = Forecasted_Demand − Available_Water`
- `WAR = Available / Forecasted` (e.g. 450/500 = 0.90)
- Stress thresholds live in config/DB table, never hardcoded. Initial values provisional until calibrated with municipality.
- MVP supply allocator: rule-based, need-ranked, never allocates > available (minus documented reserve %).

## 6. Environments
Local (Docker Postgres + `.env`) → Staging (Render/Netlify mirror) → Production pilot. Models bundled with image or pulled from object storage at boot (open decision — record choice).

## 7. Assumptions / Open Items
No repo/code yet; schema finalized at Phase 6; Transformer value vs. data size unproven; LP/MILP deferred; GIS boundaries TBD; hosting tiers TBD. All changes go to `Context.md`.
