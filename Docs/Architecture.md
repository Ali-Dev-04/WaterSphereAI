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
| Languages | Python (ML/backend), JavaScript/JSX (dashboard), Dart (app) |
| Data/ML | Pandas, NumPy, Scikit-learn, XGBoost; TF/Keras for LSTM/GRU/Transformer (PyTorch = allowed alternative, record in Context.md if switched) |
| Metrics | MAE, RMSE, MAPE, R² |
| DB | PostgreSQL + SQLAlchemy 2 + Alembic |
| API | FastAPI (routers → services → repository), Pydantic v2, JWT (`python-jose`), bcrypt (direct), slowapi |
| Dashboard | React 18 + Vite, Recharts, react-leaflet, plain CSS tokens |
| Mobile | Flutter + FCM (not built yet) |
| Deploy | Render (API+DB), Netlify (dashboard); Docker for parity (Phase 15, not started) |

## 3. API Surface (live, 22 operations — OpenAPI at `/docs`)
- **Auth:** `POST /api/auth/register` (citizen only), `POST /api/auth/login` (10/min/IP), `GET /api/auth/me`
- **Public (no token):** `GET /api/health`, `GET /api/meta` (ward count, dataset window, WAR bands, model version), `GET /api/public/wards`, `POST /api/complaints/public` (guest report, 5/min/IP, multipart + photo)
- **Read (token, ward-scoped for citizens):** `GET /api/wards`, `/api/population`, `/api/consumption`, `/api/reservoir`, `/api/forecast?ward_id&target_date&horizon`, `/api/water-stress?ward_id&date`, `/api/supply-plan?date`, `/api/gis?date`, `/api/leakage-risk`, `/api/maintenance`, `/api/model-info`
- **Complaints (token):** `GET /api/complaints` (admin: all; citizen: own), `POST /api/complaints` (citizen own ward / admin any), `PATCH /api/complaints/{cid}` (admin), `GET /api/complaints/{cid}/photo` (admin only)

Auto-generated OpenAPI is the contract. Inference loads the active model per horizon once at startup (never per request).

## 4. Database (11 tables, head `c8f2a6b1e4d9`)
`users(id, username, password_hash, role, ward_id)`, `wards(ward_id, ward_name, area_km2)`, `population(ward_id, year, population, density, growth)`, `consumption(ward_id, date, consumed_ml, supplied_ml, demand_ml)`, `reservoirs(reservoir_id, reservoir_name, lat, lon, capacity_mcm, serving_wards)`, `reservoir_readings(reservoir_id, date, level_m, storage_pct, available_water_ml)`, `forecasts(ward_id, target_date, horizon, predicted_ml, model, model_version)`, `water_stress(ward_id, date, gap_ml, war, category)`, `supply_plans(ward_id, date, allocated_ml, alert)`, `complaints(...)`, `maintenance(...)`.

`complaints` supports both authenticated citizens and guests (migration `c8f2a6b1e4d9`, additive): `user_id` nullable, plus nullable `reporter_name`, `address`, `description`, `photo_path` (server-generated filename under `uploads/`). Legacy rows remain valid; admin listing returns both kinds.

Relations: Ward → Population/Consumption/Forecast/WaterStress/SupplyPlan; Reservoir → Readings → WaterStress; Forecast + Availability → Stress → Plan.

## 5. Key Business Logic (canonical)
- `Storage% = Current / Capacity × 100`
- `Gap = Forecasted_Demand − Available_Water`
- `WAR = Available / Forecasted` (e.g. 450/500 = 0.90)
- Stress thresholds live in config/DB table, never hardcoded. Initial values provisional until calibrated with municipality.
- MVP supply allocator: rule-based, need-ranked, never allocates > available (minus documented reserve %).

## 6. Client Architecture (React dashboard)
`Landing` (public entry: hero, 3-step model, `/api/meta` stat chips, CTAs) → `Login` (sign-in | citizen registration | guest report) → dashboard shell (gov strip, masthead, ward/date context bar, role-aware tabs). All user-visible configuration (ward count, date bounds + default date, WAR bands, model version) is fetched from `/api/meta`; nothing is hardcoded in the UI. Styling is plain CSS with Design_System tokens in a light municipal theme. Admin Complaints adds an "All wards" filter with per-ward counts and a detail modal (photo fetched as an authorized blob).

## 7. Current Implementation State (2026-10-25)
- Backend, database, ML pipeline, dashboard, GIS, leakage, auth/RBAC, guest complaints: **implemented and live**.
- Verification: backend `pytest` **28/28**, live e2e **38/38**, frontend build PASS, CI green (backend + ml-smoke + frontend).
- Not started: Flutter citizen app (Phase 11), staging deploy (Phase 15), authoritative ward boundaries.

## 8. Assumptions / Open Items
- WAR thresholds are configurable (env), provisional pending municipal sign-off. `/api/water-stress` and `/api/gis` divide each reservoir's **gross `available_water_ml`, split equally among the wards that reservoir serves**, by forecast demand — so WAR values run ~10²–10³ and every ward reads Safe (`EVALUATION.md §5`); choosing servable-share availability is an open decision.
- GIS ward polygons are approximate centroid boxes until municipal GeoJSON is supplied.
- Reservoir `level_m` is a placeholder; serving-ward mapping is synthetic.
- xgboost slot runs a sklearn HGB fallback (libomp unavailable on the training host) — API-compatible.
- Open decisions are tracked in `Context.md` (hosting, observability, refresh tokens/OTP, WAR availability basis).
All changes go to `Context.md`.

## 9. Environments
Local (Docker Compose Postgres + API + Vite, or host-direct fallback: Homebrew Postgres + uvicorn with `WS_BASE`) → Staging (Render API + managed Postgres, Netlify dashboard — Phase 15, not started) → Production pilot. Models ship with the image; the registry manifest selects the active artifact per horizon.
