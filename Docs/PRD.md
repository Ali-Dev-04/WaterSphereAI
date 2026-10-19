# PRD — WaterSphere AI

## 0. Metadata
- **Product:** WaterSphere AI — AI-Powered Smart Water Management Platform
- **Stage:** Pre-development / Documentation & Research. No code, DB, or models exist yet.
- **Source docs:** `Docs/Project_Overview.md`, `Docs/WaterSphere AI_Project_Complete_Development_Context.pdf` (§1–32), `Docs/Architecture.jpeg` (11 blocks), `Docs/IMPLEMENTATION_PLAN.md`
- **Owner:** Municipal water authority (pilot municipality TBD). Developer/research team builds and validates.

## 1. Problem Statement
Municipal water demand varies by ward (population size/density). Fixed/manual supply schedules cause under-supply in some areas and over-supply in others. Population, consumption, and reservoir data exist but are not integrated for predictive planning. Demand forecasting and reservoir forecasting are treated as separate problems.

**Research question:** Can AI use population, historical consumption, reservoir availability, and temporal patterns to predict future demand and improve supply decisions?

## 2. Target Users
1. **Admin (primary):** municipal planners — view forecasts, stress zones, supply plans, GIS, leakage indicators, complaints.
2. **Operations staff:** execute supply, handle complaints/maintenance (same Admin role, ward-scoped if later decided).
3. **Citizens:** view supply schedule, receive shortage/maintenance alerts, file/track complaints.

## 3. Goals / Non-Goals
**Goals:**
- Ward-level 1-day / 3-day / 7-day demand forecasts.
- Reservoir-aware recommendations (forecast vs. available water), not raw forecasts alone.
- Early stress detection: Safe / Moderate / High Stress / Shortage via Water Availability Ratio (WAR).
- Zone-wise supply plan + shortage alerts surfaced on dashboard, GIS map, citizen app.

**Non-goals (MVP):**
- Rainfall/weather prediction (explicitly out of scope).
- LP/MILP optimization (Advanced only; MVP is rule-based).
- Multi-city support, automated retraining (Future).
- Supervised leakage classification unless labels are found (MVP = unsupervised anomaly only).

## 4. Functional Requirements
| ID | Requirement | Acceptance |
|---|---|---|
| FR1 | Ingest + merge population, consumption, reservoir, temporal on `Ward_ID + Date` | Zero duplicate ward-date rows; key-integrity assertions pass |
| FR2 | Train + compare XGBoost, LSTM, GRU, Transformer; select best | Comparison table (MAE/RMSE/MAPE/R²) fully populated; beats naive baseline on 1-day |
| FR3 | Produce 1/3/7-day forecasts per ward | `/api/forecast?ward=X&horizon=1,3,7` returns values |
| FR4 | Reservoir storage % + available water per reservoir | `Storage% = Current/Capacity*100`; visible via `/api/reservoir` |
| FR5 | Demand–supply gap + WAR per ward/period | `Gap = Forecast - Available`; `WAR = Available / Forecast`. Worked example: 500 ML / 450 ML → Gap 50, WAR 0.90 |
| FR6 | 4-category stress classification | Thresholds configurable (not hardcoded); `/api/water-stress` |
| FR7 | Zone-wise supply plan + shortage alerts | Allocates ≤100% of available water, prioritizes high-stress wards; `/api/supply-plan` |
| FR8 | Authenticated REST APIs | All endpoints in §6 behind JWT except explicitly public ones |
| FR9 | Admin dashboard (React) | Admin can log in → view forecast/stress/plan for ≥1 ward from real API data |
| FR10 | Citizen app (Flutter) | Citizen can register → view schedule/alerts → file/track complaint E2E |
| FR11 | Leakage/wastage (supporting) | `Loss = Supplied - Consumed`; IsolationForest flags visible; `/api/leakage-risk` |

## 5. Non-Functional Requirements
- **Accuracy:** report MAE/RMSE/MAPE/R² per model/ward/horizon. No pass threshold set — open decision.
- **Latency:** interactive dashboard/API; target p95 TBD (propose <1s cached).
- **Scalability:** pilot (few wards) → city-wide without schema change; stateless FastAPI + normalized PostgreSQL.
- **Auditability:** retain forecasts/decisions in PostgreSQL.
- **Maintainability:** swappable models, versioned datasets/models (`model_version`, `data_version` columns).

## 6. Scope by Release
**MVP (research core):** dataset (real or labeled-synthetic) → preprocessing → features → XGBoost + ≥1 DL model (LSTM recommended first) on 1-day + 7-day → reservoir tracking (CSV ok) → rule-based stress (provisional thresholds) → minimal FastAPI (`/forecast`, `/water-stress`) → minimal React dashboard (chart + status table) → core PostgreSQL tables (Wards, Population, Consumption, Reservoir, Forecast, WaterStress).
**Advanced:** all 4 models × 3 horizons, rule-based supply allocator (LP/MILP only if research confirms), full GIS (Leaflet+OSM), Flutter app + FCM, JWT+RBAC everywhere, complaints CRUD.
**Future:** auto-retraining + drift monitoring, supervised leakage, multi-city, weather integration, CI/CD + observability, autoscaling.

## 7. Success Metrics
- Model: comparison table complete; selected model beats seasonal-naive on test set.
- Decision: stress classification reproduces worked example; supply plan never over-allocates.
- Product: full journey passes — admin sees forecast→stress→plan → citizen gets alert → files complaint → admin sees it.
- Docs: new dev/agent onboards from `docs/` + `Context.md` alone.

## 8. Open Decisions (need human input)
Dataset municipality / real vs. synthetic; WAR threshold values; per-horizon vs. multi-output models; Transformer in MVP or deferred; rule-based vs. LP/MILP (+solver); leakage labels existence; TF/Keras vs. PyTorch; hosting tiers + Postgres provider; GIS boundary source; deadline/team; CI/CD + monitoring choice; citizen account model (self-reg vs. provisioned, OTP?).
