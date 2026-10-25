# IMPLEMENTATION PLAN
## WaterSphere AI — AI-Powered Smart Water Management Platform

---

## 0. Document Metadata

| Field | Value |
|---|---|
| **Project Name** | WaterSphere AI — AI-Powered Smart Water Management Platform for Intelligent Water Supply Planning and Leakage Risk Prediction |
| **Document Purpose** | Complete, phase-wise, dependency-aware implementation roadmap taking the project from its current (documentation/research) stage to a deployable system. Intended to be usable by any developer, AI model, or new team member without access to the original conversation. |
| **Current Project Status** | **Implemented through Phase 14.** Backend (FastAPI + PostgreSQL, 11 tables), ML pipeline + registry, React dashboard with public landing and guest complaints, GIS, leakage and auth/RBAC all exist and run. 28/28 backend tests and 38/38 live e2e checks pass; CI is green. Remaining: Phase 15 staging deploy, Phase 11 Flutter app, authoritative ward GIS, and the WAR units decision. |
| **Source Documents Reviewed** | 1. `Project_Overview.md` 2. `WaterSphere_AI_Project_Complete_Development_Context.pdf` (32 sections) 3. `Architecture.jpeg` (11-block system architecture diagram) |
| **Current Understanding** | See Section 2. |
| **Confirmed Decisions** | See Section 6 (Technology Stack) — items marked **Confirmed** were explicitly named in source docs. |
| **Assumptions** | Flagged inline as `Assumption:`. Not treated as confirmed facts. |
| **Open Questions** | Consolidated in Section 20 ("Open Decisions"). |
| **Last Updated** | 2026-10-25 — reconciled with the implemented repository. |

> **Note on this plan's status:** this document was originally written when only research/overview material existed. It is kept as the phase-by-phase roadmap and acceptance criteria, **not** as a statement of current progress. For actual status always read `Context.md`; for the implemented architecture read `Architecture.md`. Phases 1–14 are substantially complete as of 2026-10-25 (see §18).

---

## 1. Project Understanding

### 1.1 Problem Statement
Municipal water demand varies by ward due to differing population size and density. Fixed/manual supply schedules cause **under-supply in some areas and over-supply in others**. Population, consumption, and reservoir data typically exist but are **not integrated for predictive planning**, and demand forecasting is usually treated separately from reservoir/water-level forecasting.

### 1.2 Core Research Question
*Can AI use population, historical water consumption, reservoir availability, and temporal patterns to predict future water demand and help municipalities make better water-supply decisions?*

### 1.3 Proposed Solution
An AI/ML pipeline that:
1. Ingests population, historical consumption, reservoir, and time/season data.
2. Forecasts water demand at **1-day, 3-day, and 7-day** horizons using XGBoost, LSTM, GRU, and Transformer models (best model selected by evaluation metrics).
3. Compares forecast demand against reservoir availability to compute a **Water Availability Ratio (WAR)** and classify **Safe / Moderate / High Stress / Shortage**.
4. Generates a **zone-wise smart supply plan** (allocation + shortage alerts).
5. Surfaces results via an **Admin Dashboard**, **GIS visualization**, and a **Citizen Application**.

### 1.4 Objectives
- Forecast ward-level water demand accurately across three horizons.
- Provide reservoir-aware, resource-constrained supply recommendations (not just raw forecasts).
- Detect and communicate water stress before shortages occur.
- Give municipal admins and citizens actionable, geographically contextualized information.
- Provide a supporting leakage/wastage risk-detection capability.

### 1.5 Target Users
- **Municipal water authority administrators** (primary) — planning, monitoring, allocation decisions.
- **Field/operations staff** — supply execution, complaint handling.
- **Citizens** — supply schedule visibility, alerts, complaint registration.

### 1.6 Stakeholders
- Municipal corporation / water board (system owner). *`Decision Required`: which municipality/dataset this will actually target.*
- End citizens of the serviced wards.
- Project developer/research team (you).
- `TBD`: Any academic evaluator/mentor if this is a research or capstone project.

### 1.7 Core Features
| Feature | Description |
|---|---|
| Multi-horizon demand forecasting | 1/3/7-day forecasts per ward using best-of-4 ML/DL models |
| Reservoir availability analysis | Water level, storage %, available water tracking |
| Demand–supply gap analysis | Forecast vs. availability comparison |
| Water stress classification | WAR-based Safe/Moderate/High-Stress/Shortage labeling |
| Smart supply planning | Zone-wise allocation recommendations, shortage alerts |
| Admin dashboard | Forecasts, stress zones, supply plans, GIS, leakage indicators, complaints |
| GIS visualization | Ward boundaries, density, demand, stress zones, reservoirs |
| Citizen app | Supply schedule, alerts, notifications, complaint registration/tracking |
| Leakage/wastage detection (supporting) | Water-loss estimation, anomaly detection |

### 1.8 Functional Requirements
- FR1: System shall ingest and merge population, consumption, reservoir, and temporal datasets on common ward/time keys.
- FR2: System shall train and evaluate ≥4 forecasting models and select the best per evaluation metrics.
- FR3: System shall produce 1-day, 3-day, 7-day demand forecasts per ward.
- FR4: System shall compute reservoir storage percentage and available water per reservoir.
- FR5: System shall compute demand–supply gap and WAR per ward/period.
- FR6: System shall classify water stress into 4 categories using calibrated thresholds.
- FR7: System shall generate a zone-wise supply plan and shortage alerts.
- FR8: System shall expose all of the above via authenticated REST APIs.
- FR9: Admin dashboard shall visualize forecasts, stress, supply plans, and GIS layers.
- FR10: Citizen app shall show schedules/alerts and allow complaint submission/tracking.
- FR11 (supporting): System shall estimate water loss and flag anomalous consumption/supply patterns.

### 1.9 Non-Functional Requirements
- **Accuracy:** Forecast error (MAPE/RMSE) must be tracked and reported per model/ward; no fixed target yet (`Decision Required` — acceptable error threshold).
- **Latency:** Dashboard/API responses should be interactive (`Decision Required`: target p95 latency, e.g., <1s for cached queries).
- **Availability:** `TBD` — depends on hosting tier (Render/Netlify free vs. paid).
- **Scalability:** Must scale from a pilot (few wards) to city-wide (many wards) without architecture change — favors normalized PostgreSQL schema and stateless API.
- **Maintainability:** Modular ML pipeline (swappable models), versioned datasets/models.
- **Auditability:** Forecast/decision history must be retained in PostgreSQL for traceability.

### 1.10 AI/ML Requirements
Forecasting: XGBoost (tabular/tree-based), LSTM & GRU (sequential/recurrent), Transformer (attention-based, long-sequence/multi-step). Evaluated on MAE, RMSE, MAPE, R². Supporting: Random Forest/XGBoost for leakage-risk classification (when labels exist), Isolation Forest for anomaly detection.

### 1.11 Data Requirements
Ward-level, ideally daily-granularity records for: Population (ward, year, population, area, density, growth), Consumption (date, ward, consumption, supplied, demand), Reservoir (reservoir ID, date, level, capacity, current storage, storage %, available water), Time/Season (date, day, day-of-week, month, year, season, weekend flag). **`Research Required`**: no actual dataset/source has been identified yet — see Phase 1.

### 1.12 Backend / Frontend / Database / API Requirements
- **Backend:** FastAPI (Python) connecting ML models, PostgreSQL, dashboard, and mobile app.
- **Frontend (Admin):** React.js, charts via Recharts/Plotly.
- **Mobile (Citizen):** Flutter.
- **Database:** PostgreSQL — stores data, models/metadata, forecasts, plans, user interactions.
- **APIs (proposed):** `/api/population`, `/api/consumption`, `/api/reservoir`, `/api/forecast`, `/api/water-stress`, `/api/supply-plan`, `/api/leakage-risk`, `/api/complaints`.

### 1.13 External Integrations
- GIS: Leaflet.js + OpenStreetMap (no paid maps API confirmed).
- Notifications: Firebase Cloud Messaging.
- `Decision Required`: any municipal/government open-data API for population/consumption/reservoir data, or is data manually sourced/simulated?

### 1.14 Security Requirements
JWT authentication, role-based access control (Admin vs. Citizen at minimum), password hashing, all APIs authenticated except public read-only endpoints (if any). `Decision Required`: whether citizen accounts require registration/OTP, and whether admin roles need finer granularity (e.g., ward-level admin vs. super-admin).

### 1.15 Deployment Requirements
Backend/API and ML inference: Render (proposed). Frontend (React dashboard): Netlify (proposed). Mobile app: app store / APK distribution (`TBD`). Database: PostgreSQL (managed instance — `Decision Required` on provider, e.g., Render Postgres/Supabase/Neon).

### 1.16 Research Requirements
Dataset sourcing/feasibility, WAR threshold calibration for the target municipality, model comparison methodology, and (if pursued) LP/MILP formulation for supply optimization.

### 1.17 Testing Requirements
Covered fully in Section 11.

### 1.18 Scalability Requirements
Ward-based schema, model retraining pipeline that scales across added wards/reservoirs without redesign, and API layer stateless enough to horizontally scale on the hosting platform.

### 1.19 Future Enhancements
Rainfall/weather integration (explicitly out of current scope per source doc), LP/MILP-based allocation optimization, automated retraining, expanded leakage/wastage analytics, and multi-city support.

---

## 2. Current Status vs. Planned Work

> Reconciled with the repository on **2026-10-25**. Authoritative progress lives in `Context.md`.

### 2.1 Already Implemented
- **Data:** `bmc-v1` — BMC Mumbai 24 wards, daily 2023-01-01 → 2025-12-31 (26,304 consumption rows, 7,672 reservoir readings, 7 reservoirs), validated PASS.
- **ML:** preprocessing, per-ward features with chronological splits, 12 trained models (4 families × 3 horizons) plus naive/seasonal baselines, evaluation report, registry (`manifest.json`/`active.json`), per-horizon selection (1d xgb/HGB, 3d/7d gru).
- **Database:** 11 tables on PostgreSQL, Alembic migrations (head `c8f2a6b1e4d9`), seeded.
- **Backend:** 22 API operations — auth/JWT + ward-scoped RBAC, forecast, water stress (WAR), supply plan (rule + optional LP), GIS, leakage risk, maintenance, complaints (signed-in + guest), `/api/meta`, model info, health.
- **Frontend:** React 18 + Vite dashboard — public landing page, sign-in/registration/guest report, role-aware tabs, light municipal theme, CSV export.
- **Quality:** `pytest backend/tests` **28/28**, `scripts/e2e_check.py` **38/38**, frontend build PASS, CI green (backend + ml-smoke + frontend).

### 2.2 Partially Implemented
- **Deployment:** local Docker + host-direct fallback work; **staging (Phase 15) is not executed** (no Render/Netlify services yet).
- **GIS:** choropleth and reservoir markers work, but ward polygons are approximate centroid boxes — authoritative municipal GeoJSON is pending.
- **Security:** JWT/RBAC/upload validation/rate limits implemented; shared rate-limit store, managed backups and production secrets are deploy-time tasks.
- **UI:** desktop verified end-to-end; mobile-width visual sweep is outstanding.

### 2.3 Planned (remaining scope)
- **Phase 11 — Flutter citizen app** (deferred by the user): schedule, alerts, complaints, account, FCM.
- **Phase 15 — staging deploy** + runbook (API, managed Postgres, dashboard, migrations, seed, e2e against staging).
- **P2/P3 improvements:** observability (Sentry/APM), e2e in CI with ephemeral Postgres, multi-city scoping, accessibility/i18n, authoritative GIS layers.

### 2.4 Blocked
- **Staging deploy** needs hosting accounts, a fresh production `JWT_SECRET`, and a managed Postgres provider.
- **Citizen push notifications** need a Firebase project + mobile app-store accounts (Phase 11).
- **WAR availability basis** needs an owner decision: keep absolute bands over gross equal-split storage (current; all wards Safe) or switch to servable-share availability. See `EVALUATION.md §5`.

### 2.5 Research Required
- Municipal sign-off on absolute WAR thresholds (currently configurable, provisional).
- Whether weather/rainfall should be rescoped as an exogenous demand driver (explicitly out of current scope).
- Real labeled leakage incidents for supervised classification (today unsupervised `IsolationForest` only).
- Per-city WAR calibration if the pilot expands beyond Mumbai.

---

## 3. Architecture → Implementation Mapping

Derived from `Architecture.jpeg` and PDF §5, §26.

| Architecture Component | Purpose | Technology | Implementation Phase | Dependencies |
|---|---|---|---|---|
| Data Sources (Population, Density, Historical Consumption, Reservoir, Time/Season) | Raw inputs to the pipeline | CSV/DB extracts, PostgreSQL staging tables | Phase 1 (Data Acquisition) | None (entry point) |
| Preprocessing & Feature Engineering | Clean, integrate, scale, select, reduce dimensionality, align by time/ward | Pandas, NumPy, Scikit-learn | Phase 2–3 | Phase 1 |
| Data Preparation (train/val/test split) | Chronological split for time-series integrity | Pandas, custom splitter | Phase 3 | Phase 2 |
| Model Training (XGBoost, LSTM, GRU, Transformer) | Learn demand patterns from features | XGBoost, TensorFlow/Keras (or PyTorch) | Phase 4 | Phase 3 |
| Validation & Model Selection | Hyperparameter tuning, cross-validation, metric comparison | Scikit-learn, Optuna/GridSearch, MAE/RMSE/MAPE/R² | Phase 4 | Phase 4 (training) |
| Evaluation (Test set, Final model) | Confirm generalization on held-out data | Same metrics on test split | Phase 5 | Phase 4 |
| Prediction (1/3/7-day forecast) | Serve forecasts for new/current data | Serialized model + FastAPI inference endpoint | Phase 5–6 | Phase 5 |
| Reservoir Availability Analysis | Water level, storage, storage %, available water | Backend service + PostgreSQL queries | Phase 7 | Phase 6 (DB/API) |
| Demand–Supply Analysis | Forecast vs. available water gap | Backend business logic | Phase 7 | Phase 5, 7 (reservoir) |
| Water Stress Analysis | WAR calculation + category classification | Backend business logic (rule-based) | Phase 7 | Phase 7 (demand-supply) |
| Smart Supply Plan | Zone-wise allocation + shortage alerts | Backend logic (rule-based MVP) / LP-MILP (advanced) | Phase 8 | Phase 7 |
| System Outputs — Admin Dashboard | Visualize all of the above | React.js, Recharts/Plotly | Phase 9 | Phase 6 (API) |
| System Outputs — GIS Visualization | Map-based ward/reservoir/stress visualization | Leaflet.js + OpenStreetMap | Phase 10 | Phase 6 (API), Phase 9 |
| System Outputs — Citizen Application | Schedule, alerts, complaints | Flutter, Firebase Cloud Messaging | Phase 11 | Phase 6 (API) |
| Database (PostgreSQL) | Stores all data, models metadata, forecasts, plans, interactions | PostgreSQL | Phase 6 | Phase 1–5 (schema needs finalized entities) |
| Leakage/Wastage (supporting) | Water-loss estimation, anomaly detection | Random Forest/XGBoost, Isolation Forest | Phase 12 | Phase 6, historical labels (`Research Required`) |
| Authentication/Authorization | Secure API access, RBAC | JWT, FastAPI security middleware | Phase 6/14 | Phase 6 |
| Deployment Infrastructure | Host backend, frontend, DB | Render (API/DB), Netlify (frontend) | Phase 15 | All prior phases (per component) |

---

## 4. Technology Stack

| Layer | Technology | Purpose | Reason | Status |
|---|---|---|---|---|
| Programming Languages | Python, JavaScript/TypeScript, Dart | Backend/ML, web frontend, mobile app | Matches each layer's ecosystem strengths | **Confirmed** |
| Data Processing | Pandas, NumPy | Cleaning, merging, feature engineering | Standard, well-supported for tabular/time-series prep | **Confirmed** |
| Classical ML | Scikit-learn, XGBoost | Tabular forecasting, leakage classification, anomaly detection (Isolation Forest) | Strong on tabular data w/ engineered features; fast to iterate | **Confirmed** |
| Deep Learning | TensorFlow/Keras | LSTM, GRU, Transformer models | Explicitly named in source docs | **Confirmed** (PyTorch is a **Recommended alternative** if the team is more familiar with it) |
| Forecasting Models | XGBoost, LSTM, GRU, Transformer | Demand prediction, compared head-to-head | Covers tree-based + recurrent + attention paradigms for a fair comparison | **Confirmed** |
| Evaluation Metrics | MAE, RMSE, MAPE, R² | Model comparison/selection | Standard regression/forecast metrics | **Confirmed** |
| Database | PostgreSQL | Persistent store for all entities | Relational integrity for Ward/Reservoir/Forecast relationships; explicitly named | **Confirmed** |
| Backend/API | FastAPI (Python) | Serve ML models, business logic, REST APIs | Async, fast, typed, integrates naturally with the Python ML stack | **Confirmed** |
| Admin Frontend | React.js + Recharts/Plotly | Dashboard UI, charts | Explicitly named; component-based, good charting ecosystem | **Confirmed** |
| GIS | Leaflet.js + OpenStreetMap | Map visualization | Explicitly named; free/open-source, avoids paid map API costs | **Confirmed** |
| Mobile App | Flutter | Citizen application | Explicitly named; single codebase for iOS/Android | **Confirmed** |
| Authentication | JWT | Stateless auth across API/dashboard/app | Explicitly named; works well with FastAPI + mobile clients | **Confirmed** |
| Notifications | Firebase Cloud Messaging | Push alerts to citizens | Explicitly named; free tier, cross-platform | **Confirmed** |
| Deployment | Render (backend+DB), Netlify (frontend) | Hosting | Explicitly named; low-cost/managed for a pilot-scale project | **Confirmed** (Proposed — should be revisited if traffic/compute needs grow, e.g., GPU training may need a separate provider) |
| Optimization (advanced) | Linear Programming / MILP (e.g., PuLP, OR-Tools) | Zone-wise supply allocation optimization | Mentioned as an advanced-stage option in source docs | **Requires Research** — solver choice, formulation, and whether it's needed vs. rule-based allocation for MVP |
| Model/Experiment Tracking | Not specified | Track experiments/model versions across 4 model types | Needed given multi-model comparison across 3 horizons | **Requires Decision** — e.g., MLflow vs. simple CSV/DB logging |
| CI/CD | Not specified | Automate testing/deployment | Not mentioned in source docs | **Requires Decision** — e.g., GitHub Actions |
| Monitoring/Logging | Not specified | Track API health, model drift, errors | Not mentioned in source docs | **Requires Decision** |

---

## 5. AI/ML Implementation Pipeline

| Stage | Application in WaterSphere AI |
|---|---|
| 1. Problem formulation | Multi-horizon (1/3/7-day) regression: predict ward-level water demand |
| 2. Target definition | `demand_t+1`, `demand_t+3`, `demand_t+7` per ward (either 3 separate models per horizon-per-algorithm, or one multi-output/sequence model — **`Decision Required`**) |
| 3. Dataset requirements | Ward-level daily records joining population, consumption, reservoir, and calendar data (Section 1.11) |
| 4. Data collection | Phase 1 — see dataset sourcing plan below |
| 5. Data cleaning | Deduplication, missing-value handling, outlier detection, ID/date standardization (Phase 2) |
| 6. Exploratory Data Analysis | Seasonality, trend, per-ward consumption distribution, correlation of population/density with demand, reservoir depletion patterns (Phase 3) |
| 7. Feature engineering | Lag features (prev-day, prev-7-day), rolling averages (7/30-day), prev-month demand, population/density/growth, reservoir level/storage/%/available water, calendar features (Phase 3, PDF §8) |
| 8. Feature selection | Correlation/feature-importance analysis (e.g., XGBoost feature importance, mutual information) to trim redundant features per model type |
| 9. Baseline model | Naive/seasonal-naive forecast (e.g., "same as last week") and/or simple linear regression, to contextualize how much the 4 candidate models actually improve on it |
| 10. Model selection | XGBoost (tabular/lag features), LSTM & GRU (sequential), Transformer (long-range/multi-step) — trained under comparable conditions (same train/val/test split, same feature set where architecturally possible) |
| 11. Model training | Per-model, per-horizon training scripts; chronological train/val/test split (proposed 70/15/15, adjustable per dataset size) |
| 12. Hyperparameter tuning | Cross-validation (time-series aware, e.g., expanding-window CV) via GridSearch/Optuna on the validation set only |
| 13. Validation | Validation-set metrics (MAE/RMSE/MAPE/R²) drive model/hyperparameter selection, never the test set |
| 14. Model evaluation | Final, one-time evaluation of the selected model on the held-out test set |
| 15. Model comparison | Populate the comparison table (PDF §11) across all 4 models × 3 horizons |
| 16. Explainability | XGBoost: SHAP/feature-importance; LSTM/GRU/Transformer: attention weights (Transformer) or permutation importance — helps justify supply-plan recommendations to municipal staff (**Recommended**, not explicitly required in source docs) |
| 17. Model serialization | `joblib`/pickle for XGBoost; TensorFlow SavedModel/`.h5` for DL models; version-tagged filenames or a model registry |
| 18. Inference pipeline | FastAPI endpoint loads the currently "active" (best) model per horizon and serves predictions on new ward/date input |
| 19. API integration | `/api/forecast` (per Section 1.12) returns 1/3/7-day predictions per ward |
| 20. Monitoring | Track live prediction error against realized consumption once available (feedback loop) — `Decision Required` on tooling |
| 21. Retraining strategy | `Decision Required`: fixed schedule (e.g., monthly) vs. triggered by drift/error-threshold breach |

---

## 6. Research vs. Development Tracks

### Research Track
- Dataset sourcing and feasibility (municipal/open data vs. synthetic/simulated data).
- WAR threshold calibration for Safe/Moderate/High-Stress/Shortage.
- Comparative literature check on demand-forecasting model choices for small-to-medium municipal datasets (is a Transformer justified at this data scale?).
- LP/MILP formulation feasibility for the "Advanced" supply-planning stage.
- Feasibility of leakage-risk labels (does historical data contain enough signal to train Random Forest/XGBoost/Isolation Forest reliably?).

### Development Track
Everything in Phases 1–17 (Section 7).

### Research → Development Mapping

| Research Question | Finding / Decision | Development Requirement |
|---|---|---|
| Where does the population/consumption/reservoir dataset come from? | `Research Required` | Blocks Phase 1; determines schema granularity (daily vs. monthly, ward vs. city-wide) |
| What WAR thresholds define Safe/Moderate/High-Stress/Shortage? | `Decision Required` — calibrate per municipal context | Blocks Phase 7 (Water Stress Analysis) business logic |
| Is a Transformer justified given likely dataset size? | `Research Required` | Determines whether Transformer is included in MVP model comparison or deferred to Advanced |
| Rule-based vs. LP/MILP supply allocation? | `Decision Required` | Determines Phase 8 scope (MVP = rule-based; Advanced = optimization) |
| Are leakage-risk labels available? | `Research Required` | Determines whether Phase 12 is feasible as supervised classification or must start as unsupervised anomaly detection only |

---

## 7. MVP, Advanced, and Future Versions

### MVP (proves the research core — PDF §29)
- Dataset assembled (real or credible simulated data) for ≥1 municipality/ward set.
- Preprocessing + feature engineering pipeline.
- XGBoost + at least one DL model (LSTM **recommended** as the simpler DL baseline before GRU/Transformer) trained and compared on 1-day and 7-day horizons.
- Reservoir availability tracking (manual/CSV-driven acceptable for MVP).
- Water stress classification (rule-based, thresholds provisionally set and flagged as `Decision Required` for later calibration).
- Minimal FastAPI backend exposing forecast + water-stress endpoints.
- Minimal React dashboard: forecast chart + stress status per ward (table or simple map, GIS optional at MVP).
- PostgreSQL schema for core entities (Ward, Population, Consumption, Reservoir, Forecast, WaterStress).

### Advanced Version
- Full 4-model comparison (adds GRU, Transformer) across all 3 horizons.
- Smart Supply Plan module (rule-based allocation minimum; LP/MILP optimization if research confirms feasibility).
- Full GIS visualization (Leaflet + OSM layers for density/demand/stress/reservoirs).
- Citizen application (Flutter) with schedule/alerts.
- JWT auth + RBAC across all APIs.
- Complaint management (submission + tracking).

### Future / Production Version
- Automated retraining pipeline with drift monitoring.
- Leakage/wastage detection module (Random Forest/XGBoost + Isolation Forest) once labeled/enough historical data exists.
- LP/MILP-based allocation optimization (if not already in Advanced).
- Multi-municipality/multi-city support.
- Rainfall/weather data integration (explicitly deferred per source doc's scope decision).
- CI/CD, full observability/monitoring stack, autoscaling.

---

## 8. Phase-Wise Implementation Roadmap

> Ordering follows the project's own recommended development priority (PDF §29): **Dataset → Preprocessing → Feature Engineering → AI Forecasting → Demand Forecast → Reservoir Availability → Water Stress → Smart Supply Planner → Dashboard/GIS/Citizen App → Leakage/Wastage/Complaints/Notifications.**

### Phase 1 — Data Acquisition & Dataset Assembly
- **Objective:** Obtain or construct ward-level population, consumption, reservoir, and temporal datasets.
- **Purpose in the Project:** Every downstream phase (features, models, forecasts) depends entirely on this data existing and being joinable on ward/time keys. This is the single hardest blocker today since no dataset was found in the workspace.
- **Tasks:**
  1. Decide target municipality/region (or confirm a synthetic/simulated dataset is acceptable for a prototype).
  2. Search government/open-data portals (e.g., city water-board open data, census data for population/density) for real data.
  3. If real data is unavailable/insufficient, design a **rule-based synthetic data generator** that mimics realistic seasonal demand, population growth, and reservoir drawdown patterns.
  4. Define the join key (`Ward_ID + Date` per source docs) and confirm every dataset can be aligned to it.
  5. Document data provenance, licensing, and update frequency.
- **Implementation Approach:** Start with a feasibility spike — pull sample records from candidate sources, verify ward-level granularity actually exists (many public sources are city-level only, not ward-level). Fall back to synthetic generation calibrated against any real aggregate statistics found (e.g., city-level per-capita consumption).
- **Technology:** Python (`requests`/`pandas` for scraping/loading), CSV/Excel/API sources, `Faker`/custom scripts for synthetic data if needed.
- **Inputs:** None (entry point).
- **Outputs/Deliverables:** Raw population, consumption, reservoir, and calendar datasets (files or DB tables) with a documented schema and data dictionary.
- **Dependencies:** None.
- **Acceptance Criteria:** All four data categories exist, share a common ward/time key, and cover a long enough period to support 7-day-ahead forecasting with a meaningful train/val/test split (`Decision Required`: minimum history length, e.g., ≥1–2 years of daily data recommended for seasonal patterns).
- **Risks:** Real ward-level data may not exist publicly; synthetic data may not generalize to real deployment.
- **Mitigation:** Clearly label synthetic-data results as a **proof-of-concept**, not production-validated; keep the pipeline data-source-agnostic so real data can be swapped in later without redesign.

### Phase 2 — Data Preprocessing & Integration
- **Objective:** Produce a single, clean, integrated dataset ready for feature engineering.
- **Purpose in the Project:** Raw multi-source data will have inconsistent IDs, missing values, and outliers; without this phase, models will learn noise instead of signal.
- **Tasks:** Deduplicate records; handle missing values (imputation strategy per field); detect/handle outliers (e.g., IQR or z-score on consumption); standardize date formats and ward/zone IDs; merge all four sources on `Ward_ID + Date`; normalize/scale numeric features where required.
- **Implementation Approach:** Build a reusable preprocessing pipeline (not ad-hoc notebook code) as importable Python modules so it can run identically in training and inference. Log data-quality metrics (missing % per field, outliers removed) for auditability.
- **Technology:** Pandas, NumPy, Scikit-learn (`SimpleImputer`, `StandardScaler`/`MinMaxScaler`).
- **Inputs:** Raw datasets from Phase 1.
- **Outputs/Deliverables:** One clean, merged, ward-date-indexed dataset; a data-quality report.
- **Dependencies:** Phase 1.
- **Acceptance Criteria:** Zero duplicate ward-date rows; documented missing-value policy applied consistently; merged dataset row count matches expected ward × date coverage.
- **Risks:** Misaligned keys across sources silently drop/duplicate rows.
- **Mitigation:** Add automated row-count/key-integrity assertions after each merge step.

### Phase 3 — Feature Engineering & Dataset Creation
- **Objective:** Engineer predictive features and produce chronologically split train/validation/test sets.
- **Purpose in the Project:** Lag/rolling features are what let tree-based models like XGBoost capture temporal patterns without recurrence; this phase is what differentiates a naive forecast from a genuinely predictive one.
- **Tasks:** Build population features (population, density, growth); consumption features (prev-day, prev-7-day, 7-day rolling avg, 30-day rolling avg, prev-month demand); reservoir features (level, storage, storage %, available water); temporal features (month, day, day-of-week, year, season, weekend flag); perform EDA to sanity-check feature/target relationships; split chronologically (proposed 70/15/15).
- **Implementation Approach:** Compute lag/rolling features **per ward** (never across wards) to avoid leakage; ensure the split is time-based (no shuffling) so validation/test always follow training in time.
- **Technology:** Pandas (`.shift()`, `.rolling()`), NumPy, Matplotlib/Seaborn for EDA.
- **Inputs:** Clean merged dataset (Phase 2).
- **Outputs/Deliverables:** Final modeling dataset with all engineered features; train/val/test splits saved as versioned files/tables; EDA report/notebook.
- **Dependencies:** Phase 2.
- **Acceptance Criteria:** No feature computed using future information relative to its row's date (no leakage); split boundaries documented; feature set reviewed against PDF §8 checklist.
- **Risks:** Data leakage via improperly computed rolling/lag features; insufficient history for 30-day rolling features early in the series.
- **Mitigation:** Unit-test feature functions on synthetic known inputs; drop/flag rows where rolling windows are incomplete rather than filling with misleading zeros.

### Phase 4 — AI/ML Model Development (Training)
- **Objective:** Train XGBoost, LSTM, GRU, and Transformer models for each forecast horizon.
- **Purpose in the Project:** This is the research core of the project — the comparison itself is the deliverable, not just the "best" model.
- **Tasks:** Build baseline (naive/seasonal-naive) forecast; implement XGBoost regressor per horizon; implement LSTM and GRU sequence models (windowed sequences per ward); implement Transformer model for long-sequence/multi-step forecasting; run time-series-aware cross-validation and hyperparameter tuning for each.
- **Implementation Approach:** Use a consistent train/val/test split and, where feasible, an overlapping feature set (lag/rolling/exogenous features) across model types so the comparison is fair; for LSTM/GRU/Transformer, construct fixed-length input windows (e.g., past 14–30 days) per ward as sequence inputs.
- **Technology:** XGBoost; TensorFlow/Keras (or PyTorch, **Recommended alternative**) for LSTM/GRU/Transformer; Optuna/GridSearchCV for tuning.
- **Inputs:** Train/val/test datasets (Phase 3).
- **Outputs/Deliverables:** Four trained model families × 3 horizons (or a documented alternative such as one multi-output model per family — `Decision Required`), each with logged validation metrics.
- **Dependencies:** Phase 3.
- **Acceptance Criteria:** All four models trained and beat the naive baseline on validation MAE/RMSE for at least the 1-day horizon; training/evaluation code is reproducible (fixed seeds, versioned configs).
- **Risks:** Deep-learning models (especially Transformer) may overfit or underperform simpler models on a small ward-level dataset; GPU/compute availability for DL training.
- **Mitigation:** Always keep the naive baseline and XGBoost as a "floor"; if DL models underperform, that is itself a valid, reportable research finding — do not force their inclusion into production if they add no value.

### Phase 5 — Model Evaluation & Selection
- **Objective:** Evaluate all trained models on the held-out test set and select the best model per horizon.
- **Purpose in the Project:** Ensures the model going into production actually generalizes, and produces the comparison table required by the project's research contribution (PDF §11, §27).
- **Tasks:** Compute MAE/RMSE/MAPE/R² for every model × horizon on the test set (single pass, no re-tuning after seeing test results); populate the comparison table; select and document the best model per horizon; save the winning models to a model registry/serialized store.
- **Implementation Approach:** Automate this as a script/notebook that takes all trained model artifacts and produces the comparison table + a written justification for the selection (not just "lowest RMSE" — also consider inference latency and interpretability where relevant to the smart supply plan).
- **Technology:** Scikit-learn metrics, Pandas for the report, `joblib`/TensorFlow save formats for the winning models.
- **Inputs:** Trained models (Phase 4), test split (Phase 3).
- **Outputs/Deliverables:** Populated model comparison table (PDF §11 template); serialized "active" model(s) per horizon; selection rationale document.
- **Dependencies:** Phase 4.
- **Acceptance Criteria:** Comparison table fully populated (no blank cells); selected model(s) clearly identified and saved in a loadable format for Phase 6.
- **Risks:** Test-set leakage if evaluation is run multiple times with retuning in between.
- **Mitigation:** Lock the test set and only touch it once per model-selection cycle; keep validation and test evaluation code physically separate.

### Phase 6 — Database & Backend/API Development
- **Objective:** Stand up the PostgreSQL schema and FastAPI backend, including model inference serving and authentication.
- **Purpose in the Project:** This is the integration backbone — dashboard, GIS, and citizen app all depend on this layer, and it is where the "smart" outputs (forecast, stress, supply plan) get persisted and served.
- **Tasks:**
  1. Design PostgreSQL schema: `Users`, `Wards`, `Population`, `Consumption`, `Reservoir`, `Forecast`, `WaterStress`, `SupplyPlan`, `Complaints`, `Maintenance` (PDF §22–23).
  2. Implement FastAPI project structure (routers, models/schemas via Pydantic, DB session management).
  3. Implement JWT authentication and role-based access control (Admin/Citizen).
  4. Implement `/api/population`, `/api/consumption`, `/api/reservoir`, `/api/forecast`, `/api/water-stress`, `/api/supply-plan`, `/api/leakage-risk`, `/api/complaints`.
  5. Build the model-inference service that loads the "active" model per horizon (from Phase 5) and serves predictions on demand.
- **Implementation Approach:** Layered architecture — routers → services (business logic, e.g., WAR calculation) → repository/DB layer. Inference service should be decoupled (e.g., a separate module/service) so models can be swapped/retrained without touching API route code.
- **Technology:** FastAPI, SQLAlchemy/SQLModel (ORM), Pydantic (validation), PostgreSQL, `python-jose`/`passlib` for JWT/hashing, Alembic for migrations.
- **Inputs:** Finalized schema entities (informed by Phases 1–5 data shape); selected models (Phase 5).
- **Outputs/Deliverables:** Running FastAPI service with documented OpenAPI spec (auto-generated by FastAPI); populated/migratable PostgreSQL schema; working `/api/forecast` returning real predictions.
- **Dependencies:** Phase 5 (for forecast endpoint), Phases 1–3 (for schema shape of Population/Consumption/Reservoir).
- **Acceptance Criteria:** All listed endpoints return correct, authenticated responses; schema supports the Ward → Population/Consumption/Forecast/WaterStress/SupplyPlan and Reservoir → Availability → WaterStress relationships (PDF §22); Alembic migrations exist and are reproducible.
- **Risks:** Schema churn as feature requirements evolve; inference latency if models are reloaded per request.
- **Mitigation:** Design schema with soft extensibility (e.g., JSONB metadata columns) for fields not yet finalized; cache/load models once at service startup, not per request.

### Phase 7 — Water Stress & Demand-Supply Analysis Engine
- **Objective:** Implement reservoir availability analysis, demand–supply gap calculation, and water-stress classification.
- **Purpose in the Project:** This converts a raw forecast number into the decision-support insight the project is actually meant to deliver — "is there a problem, and how severe."
- **Tasks:** Implement `Storage % = (Current Storage / Total Capacity) × 100`; implement demand–supply gap = `Forecasted Demand − Available Water`; implement `WAR = Available Water / Forecasted Demand`; implement threshold-based classification into Safe/Moderate/High-Stress/Shortage; persist results to the `WaterStress` table via `/api/water-stress`.
- **Implementation Approach:** Keep thresholds in a configurable location (DB table or config file), not hardcoded, since they are explicitly flagged as needing calibration per municipal context (PDF §15).
- **Technology:** FastAPI service layer (Python), PostgreSQL.
- **Inputs:** Forecast values (Phase 5/6), reservoir data (Phase 1/2).
- **Outputs/Deliverables:** Working water-stress classification available per ward/period via API.
- **Dependencies:** Phase 6.
- **Acceptance Criteria:** Given the worked example in PDF §14/§15 (500 ML forecast, 450 ML available → WAR 0.90), the system reproduces the same gap/WAR values; classification thresholds are documented and adjustable without code changes.
- **Risks:** Uncalibrated thresholds could mislabel stress severity, undermining trust in the system.
- **Mitigation:** Treat initial thresholds as provisional/MVP-only and explicitly flag them as `Decision Required` for validation with real municipal stakeholders before any production use.

### Phase 8 — Smart Supply Planning Engine
- **Objective:** Convert water-stress results into zone-wise supply allocation recommendations and shortage alerts.
- **Purpose in the Project:** This is the actionable output of the whole pipeline — the point where forecasting turns into a decision the municipality can act on.
- **Tasks (MVP):** Rule-based allocation — e.g., prioritize wards by stress severity, allocate available reservoir water proportionally or by need-based ranking; generate shortage alerts for High-Stress/Shortage wards.
- **Tasks (Advanced):** Formulate and solve an LP/MILP problem — minimize supply deficit subject to available water and zone-level requirement constraints (PDF §16).
- **Implementation Approach:** Start with a transparent, explainable rule-based allocator for MVP (easier to validate and trust); introduce LP/MILP only after the research track confirms feasibility and value over the rule-based approach.
- **Technology:** Python business logic (MVP); PuLP or Google OR-Tools (Advanced, `Requires Research`).
- **Inputs:** Water-stress results (Phase 7).
- **Outputs/Deliverables:** `SupplyPlan` records per ward/period via `/api/supply-plan`; shortage alert events.
- **Dependencies:** Phase 7.
- **Acceptance Criteria:** For a given set of ward stress levels and total available water, the plan allocates 100% of available water (or a documented reserve %) without exceeding it, and prioritizes higher-stress wards.
- **Risks:** LP/MILP formulation complexity/solver overhead may be disproportionate to project stage.
- **Mitigation:** Explicitly scope LP/MILP as an Advanced/Future item, not an MVP blocker.

### Phase 9 — Admin Dashboard (React) Development
- **Objective:** Build the web dashboard for municipal administrators.
- **Purpose in the Project:** Primary interface for the system's core users; without it, forecasts/plans are only accessible via raw API calls.
- **Tasks:** Auth (login) screens; demand-forecast views (charts per ward/horizon); reservoir/population status views; water-stress zone views; smart supply-plan views; GIS map embed (Phase 10 integration point); leakage/wastage indicator views; complaint management views.
- **Implementation Approach:** Component-based React app consuming the FastAPI backend via a typed API client; charts via Recharts or Plotly per source doc.
- **Technology:** React.js, Recharts/Plotly, Axios/Fetch, React Router, a CSS framework (`Decision Required`, e.g., Tailwind/MUI).
- **Inputs:** Working backend APIs (Phase 6–8).
- **Outputs/Deliverables:** Deployable React app covering the feature list in PDF §18.
- **Dependencies:** Phase 6, 7, 8.
- **Acceptance Criteria:** Admin can log in, view forecasts/stress/supply plans for at least one ward end-to-end, and see it reflect real backend data (not mocked).
- **Risks:** Scope creep building every dashboard feature before the MVP forecast/stress flow is proven.
- **Mitigation:** Build dashboard incrementally against the MVP scope (Section 7) first; add leakage/complaints views only after MVP is validated.

### Phase 10 — GIS Module Integration
- **Objective:** Add map-based visualization of wards, density, demand, stress, and reservoirs.
- **Purpose in the Project:** Water stress and supply decisions are inherently geographic; a table of numbers is far less actionable than a map for municipal planners.
- **Tasks:** Obtain/create ward boundary geodata (GeoJSON); render base map via Leaflet + OpenStreetMap tiles; overlay ward polygons colored by stress category; add reservoir location markers; add population-density choropleth layer.
- **Implementation Approach:** Embed Leaflet within the React dashboard (`react-leaflet`); source ward boundaries from open government GIS data if available, otherwise approximate/placeholder polygons (`Research Required`).
- **Technology:** Leaflet.js, `react-leaflet`, OpenStreetMap tiles, GeoJSON.
- **Inputs:** Ward boundary data (`Research Required` — source `TBD`), water-stress/reservoir data (Phase 7).
- **Outputs/Deliverables:** Interactive map layer inside the admin dashboard.
- **Dependencies:** Phase 9, ward boundary data acquisition.
- **Acceptance Criteria:** Map correctly renders ward polygons colored by current stress status and reservoir markers with popups showing key stats.
- **Risks:** Ward-level GeoJSON boundaries may not be publicly available for the chosen municipality.
- **Mitigation:** Fall back to a simplified/illustrative ward grid for MVP if authoritative boundaries are unavailable, clearly labeled as approximate.

### Phase 11 — Citizen Application (Flutter) Development
- **Objective:** Build the citizen-facing mobile app.
- **Purpose in the Project:** Delivers transparency and alerts directly to residents, closing the loop from municipal planning to citizen impact.
- **Tasks:** Auth/registration; supply-schedule view; shortage/maintenance alert notifications (Firebase Cloud Messaging); complaint registration and status tracking.
- **Implementation Approach:** Flutter app consuming the same FastAPI backend (citizen-scoped endpoints/roles); push notifications via FCM tied to ward-level alerts generated in Phase 8.
- **Technology:** Flutter/Dart, Firebase Cloud Messaging, HTTP client (`dio`/`http` package).
- **Inputs:** Working backend APIs with citizen-role auth (Phase 6), alert events (Phase 8).
- **Outputs/Deliverables:** Installable Flutter app (APK/TestFlight build) covering PDF §19 features.
- **Dependencies:** Phase 6, 8.
- **Acceptance Criteria:** Citizen can register, view their ward's schedule/alerts, and submit/track a complaint end-to-end.
- **Risks:** App-store distribution overhead/timelines; FCM setup complexity.
- **Mitigation:** For MVP/demo purposes, distribute via direct APK / internal testing tracks rather than full store release.

### Phase 12 — Supporting Modules: Leakage/Wastage Detection & Complaints
- **Objective:** Add water-loss estimation, anomaly detection, and complaint management.
- **Purpose in the Project:** Explicitly scoped as a **supporting** module (PDF §20) — valuable but secondary to the core forecasting/stress/supply pipeline.
- **Tasks:** Compute `Water Loss = Water Supplied − Water Consumed`; train Random Forest/XGBoost for leakage-risk classification **if** historical leakage labels exist; apply Isolation Forest for unsupervised anomaly flagging on supply/consumption patterns; implement complaint CRUD + status tracking tied to citizen accounts.
- **Implementation Approach:** Start with unsupervised anomaly detection (Isolation Forest) since it needs no labels; add supervised leakage classification only once/if labeled incident data is confirmed available.
- **Technology:** Scikit-learn (Random Forest, Isolation Forest), XGBoost, FastAPI/PostgreSQL for complaints.
- **Inputs:** Consumption/supply data (Phase 1/2); historical leakage labels (`Research Required`).
- **Outputs/Deliverables:** `/api/leakage-risk` endpoint; `/api/complaints` endpoint; dashboard indicators (Phase 9 integration).
- **Dependencies:** Phase 6.
- **Acceptance Criteria:** Anomaly flags are generated on at least the synthetic/available dataset and visible on the dashboard; complaint records can be created, updated, and queried by status.
- **Risks:** Lack of labeled leakage incidents makes supervised classification infeasible.
- **Mitigation:** Treat this module's supervised component as Future scope if labels are unavailable; ship the unsupervised anomaly detector as the interim MVP capability.

### Phase 13 — System Integration & End-to-End Testing
- **Objective:** Verify all components (ML, backend, dashboard, GIS, mobile app) work together correctly.
- **Purpose in the Project:** Individual phases can each "work" in isolation while still failing when combined (e.g., a schema mismatch between the forecast service and the dashboard chart component).
- **Tasks:** Integrate all APIs into the dashboard and mobile app; verify data flow: data → forecast → stress → supply plan → dashboard/GIS/citizen app; run full test suite (Section 11).
- **Implementation Approach:** Use a staging environment with realistic (or synthetic) end-to-end data to validate the full pipeline before touching production/deployment.
- **Technology:** Pytest (backend), Jest/React Testing Library (frontend), Flutter test framework (mobile), Postman/HTTPie for manual API checks.
- **Inputs:** All prior phase outputs.
- **Outputs/Deliverables:** Passing end-to-end test suite; a working staging deployment.
- **Dependencies:** Phases 1–12.
- **Acceptance Criteria:** A full user journey (admin views forecast → sees stress zone → sees supply plan → citizen receives alert → citizen files complaint → admin sees complaint) completes without manual intervention.
- **Risks:** Integration bugs discovered late are costly to fix.
- **Mitigation:** Integrate incrementally per phase rather than only at the end (i.e., wire dashboard to backend as soon as Phase 6/7 land, not after Phase 12).

### Phase 14 — Security & Reliability Hardening
- **Objective:** Harden authentication, authorization, input validation, and error handling before deployment.
- **Purpose in the Project:** The system handles municipal infrastructure data and citizen personal data (complaints); security gaps here have real-world consequences.
- **Tasks:** Enforce JWT expiry/refresh; enforce RBAC on every endpoint (admin vs. citizen scopes); validate all API inputs (Pydantic schemas); rate-limit public-facing endpoints; secure secrets (env vars, not hardcoded); add structured error handling/logging.
- **Implementation Approach:** Security review pass across all Phase 6 endpoints before deployment; automated dependency vulnerability scanning.
- **Technology:** FastAPI security utilities, `python-jose`, `passlib[bcrypt]`, `slowapi` (rate limiting) or platform-level rate limiting, environment-variable management (`.env` + secret manager on Render).
- **Inputs:** Completed backend (Phase 6).
- **Outputs/Deliverables:** Security checklist signed off; hardened backend.
- **Dependencies:** Phase 6.
- **Acceptance Criteria:** No endpoint accessible without appropriate role; no secrets committed to version control; basic penetration/security test checklist passes (Section 11).
- **Risks:** Security added as an afterthought is often incomplete.
- **Mitigation:** Bake JWT/RBAC into Phase 6 from the start rather than treating this phase as a bolt-on (this phase then becomes primarily a review/audit pass).

### Phase 15 — Deployment
- **Objective:** Deploy backend, database, and frontend to production/staging environments.
- **Purpose in the Project:** Makes the system actually usable outside the development machine.
- **Tasks:** Provision PostgreSQL (Render Postgres or equivalent — `Decision Required`); deploy FastAPI backend to Render; deploy React dashboard to Netlify; configure environment variables/secrets on both platforms; set up basic logging/error alerting; document the deployment process.
- **Implementation Approach:** Deploy a staging environment first (Phase 13 dependency), then promote to production once end-to-end tests pass.
- **Technology:** Render (API + DB), Netlify (frontend), GitHub (source control triggering deploys — `Recommended`).
- **Inputs:** Fully tested application (Phase 13, 14).
- **Outputs/Deliverables:** Publicly (or municipally) accessible dashboard URL and API base URL; deployment runbook.
- **Dependencies:** Phases 6, 9, 13, 14.
- **Acceptance Criteria:** Deployed dashboard successfully calls deployed API and displays real data; deployed mobile app (if distributed) successfully calls the same API.
- **Risks:** Free/low-cost hosting tiers may have cold-start latency or resource limits unsuitable for production municipal use.
- **Mitigation:** Treat Render/Netlify as the pilot/demo deployment target; flag scaling to dedicated infrastructure as a Future item if the project moves beyond pilot stage.

### Phase 16 — Documentation & Evaluation
- **Objective:** Document the system and evaluate it against the original research question and objectives.
- **Purpose in the Project:** Required for the project to be usable/maintainable by others and to substantiate its research contribution (PDF §27).
- **Tasks:** Write technical documentation (architecture, API reference, schema); write a project report/evaluation against the model comparison table and objectives; update this Implementation Plan's Change Log; document known limitations.
- **Implementation Approach:** Keep documentation living in the repository's `docs/` folder (this file included) rather than only in conversation history.
- **Technology:** Markdown, FastAPI's auto-generated OpenAPI docs.
- **Inputs:** All completed phases.
- **Outputs/Deliverables:** `docs/` folder with architecture, API, schema, and evaluation documentation.
- **Dependencies:** Phases 1–15.
- **Acceptance Criteria:** A new developer/AI model could onboard using only the `docs/` folder.
- **Risks:** Documentation drifts from actual implementation over time.
- **Mitigation:** Update the Change Log (Section 17) and this plan whenever a phase's actual implementation deviates from what's written here.

### Phase 17 — Future Enhancements (Post-Launch)
- **Objective:** Track and plan enhancements beyond the initial deployable system.
- **Purpose in the Project:** Prevents scope creep during MVP/Advanced development while preserving good ideas for later.
- **Tasks/Items:** Rainfall/weather integration; automated retraining pipeline with drift detection; LP/MILP allocation optimization (if not done in Advanced); multi-city/multi-municipality support; expanded leakage/wastage supervised modeling; CI/CD pipeline; full observability stack (metrics/alerting).
- **Implementation Approach:** Maintain as a backlog, re-prioritized after MVP/Advanced evaluation (Phase 16).
- **Technology:** `TBD` per item.
- **Inputs:** Phase 16 evaluation results.
- **Outputs/Deliverables:** Prioritized backlog document.
- **Dependencies:** Phase 16.
- **Acceptance Criteria:** N/A (backlog, not a delivered feature).
- **Risks:** N/A.
- **Mitigation:** N/A.

---

## 9. Development Dependencies

### Must Be Completed First
Phase 1 (Data Acquisition) → Phase 2 (Preprocessing) → Phase 3 (Feature Engineering) — strictly sequential, each blocks the next.

### Can Run in Parallel
- Database schema design (Phase 6, schema portion) can start as soon as Phase 1's data shape is known, in parallel with Phase 2–4.
- GIS ward-boundary sourcing (Phase 10 research) can start any time, in parallel with everything else.
- Dashboard UI shell/design and Flutter app shell (auth screens, navigation) can be scaffolded in parallel with backend development (Phase 9/11), then wired to real APIs once Phase 6 is ready.
- Security/JWT design (Phase 14 planning) can happen in parallel with early backend work, to be built into Phase 6 rather than bolted on later.

### Backend Dependencies
- Phase 7 (Water Stress) and Phase 8 (Supply Plan) depend on Phase 6 (DB/API) and Phase 5 (selected models).
- Phase 12 (Leakage/Complaints) depends on Phase 6.

### AI/ML Dependencies
- Phase 4 (Training) depends on Phase 3 (Feature Engineering).
- Phase 5 (Evaluation/Selection) depends on Phase 4.
- Phase 6's inference service depends on Phase 5's serialized models.

### Frontend Dependencies
- Phase 9 (Dashboard) and Phase 11 (Citizen App) functionally depend on Phase 6 (working APIs), though UI shells can be built earlier.
- Phase 10 (GIS) depends on Phase 9 (dashboard shell exists) and ward boundary data.

### Final Integration
Phase 13 (Integration & E2E Testing) can only start once Phases 6–12 each have a working, independently-testable version.

---

## 10. Testing Strategy

| Test Type | Scope |
|---|---|
| **Unit Testing** | Feature-engineering functions (lag/rolling calculations), WAR/stress classification logic, supply-allocation logic, individual React components, Flutter widgets. |
| **Integration Testing** | FastAPI ↔ PostgreSQL; backend ↔ model-inference service; dashboard ↔ backend API; mobile app ↔ backend API. |
| **API Testing** | All endpoints in Section 1.12 — correct status codes, request/response schema validation, auth-required behavior, error responses. |
| **AI/ML Testing** | Data validation (schema/range checks on inputs); model performance vs. baseline; generalization (test-set metrics vs. validation-set metrics gap); edge cases (ward with sparse history, missing reservoir reading); data-leakage checks (no future info in features); prediction consistency (same input → same output for deterministic models). |
| **Frontend Testing** | Dashboard renders forecast/stress/supply-plan views correctly for sample data; responsive layout check; basic accessibility check (labels, contrast) where applicable. |
| **End-to-End Testing** | Full user journeys per Phase 13 acceptance criteria. |
| **Performance Testing** | API response latency under expected concurrent load (`Decision Required`: expected load, since this is a pilot-scale system); model inference latency per request. |
| **Security Testing** | Auth bypass attempts, RBAC boundary checks, input-validation/injection checks, secret-exposure checks. |
| **User Acceptance Testing** | Validate against Section 1.8 Functional Requirements with an actual (or simulated) municipal admin user; validate citizen-app flows with a test citizen user. |

---

## 11. Deployment Plan

| Environment | Purpose | Notes |
|---|---|---|
| **Local Development** | Individual development/testing | `.env`-based config, local PostgreSQL (Docker recommended) |
| **Testing/Staging** | Phase 13 integration testing | Mirrors production config on Render/Netlify at reduced scale |
| **Production** | Live pilot deployment | Render (API + DB) + Netlify (dashboard); mobile app via APK/store |

- **Database deployment:** Managed PostgreSQL instance (Render Postgres or equivalent), with Alembic migrations run on deploy.
- **Backend deployment:** FastAPI app containerized (Docker recommended even if Render can run it natively, for local/staging parity) and deployed to Render.
- **Frontend deployment:** React app built and deployed to Netlify, pointed at the deployed API base URL via environment config.
- **AI model deployment:** Serialized models bundled with or fetched by the backend service at startup; **`Decision Required`**: models shipped with the backend image vs. stored in object storage and pulled at boot.
- **Environment variables/secrets:** DB connection string, JWT secret, Firebase credentials, CORS origins — managed via Render/Netlify environment settings, never committed to source control.
- **Logging/monitoring/error handling:** `Decision Required` — minimum viable: structured logging + Render's built-in log viewer for MVP; upgrade path to a dedicated tool (e.g., Sentry) noted as Future.
- **Backup/recovery:** `Decision Required` — rely on managed Postgres provider's backup features at minimum.
- **Version control/CI-CD:** Git repository (GitHub recommended); CI/CD pipeline is currently `Requires Decision` — GitHub Actions running tests pre-deploy is the recommended starting point.

---

## 12. Project Management

### 12.1 Work Breakdown Structure (Phase → Module → Task)
Each Phase in Section 8 already decomposes into Tasks; Modules map to phases as follows:
- **Data Module:** Phases 1–3
- **ML Module:** Phases 4–5
- **Platform Module:** Phase 6
- **Decision-Engine Module:** Phases 7–8
- **Client Module:** Phases 9–11
- **Supporting Module:** Phase 12
- **Quality & Release Module:** Phases 13–15
- **Knowledge Module:** Phases 16–17

### 12.2 Priority

| Priority | Phases |
|---|---|
| **Critical** | 1 (Data Acquisition), 2 (Preprocessing), 3 (Feature Engineering), 4 (Model Training), 5 (Evaluation), 6 (DB/Backend), 7 (Water Stress) |
| **High** | 8 (Supply Plan), 9 (Admin Dashboard), 13 (Integration/Testing), 14 (Security), 15 (Deployment) |
| **Medium** | 10 (GIS), 11 (Citizen App), 16 (Documentation) |
| **Low** | 12 (Leakage/Wastage — supporting), 17 (Future Enhancements) |

### 12.3 Milestones
1. **Dataset Ready** — Phase 1 complete.
2. **Feature Pipeline Ready** — Phase 3 complete.
3. **Model Validated** — Phase 5 complete (comparison table populated, best model selected).
4. **Backend MVP** — Phase 6 + 7 complete (forecast + stress endpoints live).
5. **Supply Plan Ready** — Phase 8 complete.
6. **Frontend MVP** — Phase 9 complete (dashboard shows real forecast/stress data).
7. **Integration Complete** — Phase 13 complete.
8. **Testing Complete** — Section 10 test suite passing.
9. **Deployment Ready** — Phase 15 staging deploy successful.
10. **Final Release (MVP)** — Production deployment live and validated per Phase 13 acceptance criteria.
11. **Advanced Release** — Phases 8 (LP/MILP), 10, 11, 14 fully complete.

### 12.4 Definition of Done (by module)
- **Data Module:** Clean, versioned dataset with documented schema and a passing data-quality report.
- **ML Module:** Comparison table fully populated; selected model(s) serialized and loadable by the backend.
- **Platform Module:** All Section 1.12 endpoints implemented, authenticated, and covered by API tests.
- **Decision-Engine Module:** Water-stress and supply-plan outputs match manually verified example calculations.
- **Client Module:** Each client (dashboard/app) completes its full acceptance-criteria user journey (Phase 9/10/11).
- **Quality & Release Module:** Full test suite green; staging and production deployments both verified working.

---

## 13. Timeline

`Timeline requires confirmation based on the actual project deadline.`

No deadline was provided in any reviewed document. The table below gives **relative effort ordering and dependency chaining only** — durations are intentionally left as `TBD` pending a real deadline/team size/availability input.

| Phase | Duration | Dependencies | Major Deliverable |
|---|---|---|---|
| 1. Data Acquisition | `TBD` | — | Assembled dataset |
| 2. Preprocessing | `TBD` | Phase 1 | Clean merged dataset |
| 3. Feature Engineering | `TBD` | Phase 2 | Modeling-ready dataset |
| 4. Model Training | `TBD` | Phase 3 | Trained models (4 types) |
| 5. Evaluation/Selection | `TBD` | Phase 4 | Comparison table + selected model |
| 6. DB/Backend/API | `TBD` | Phases 1, 5 | Working FastAPI + PostgreSQL |
| 7. Water Stress Engine | `TBD` | Phase 6 | Stress classification live |
| 8. Supply Plan Engine | `TBD` | Phase 7 | Supply-plan output live |
| 9. Admin Dashboard | `TBD` | Phase 6–8 | Working dashboard MVP |
| 10. GIS Module | `TBD` | Phase 9 | Map visualization |
| 11. Citizen App | `TBD` | Phase 6, 8 | Working Flutter app |
| 12. Leakage/Complaints | `TBD` | Phase 6 | Leakage flags + complaint flow |
| 13. Integration & Testing | `TBD` | Phases 1–12 | Passing E2E suite |
| 14. Security Hardening | `TBD` | Phase 6 | Signed-off security checklist |
| 15. Deployment | `TBD` | Phases 13, 14 | Live staging/production system |
| 16. Documentation & Evaluation | `TBD` | Phases 1–15 | Complete `docs/` folder |
| 17. Future Enhancements | `TBD` (backlog) | Phase 16 | Prioritized backlog |

---

## 14. Resource Requirements

| Resource | Classification | Notes |
|---|---|---|
| Python 3.x environment | Mandatory | Backend/ML |
| PostgreSQL instance | Mandatory | Local (dev) + managed (prod) |
| Node.js + npm/yarn | Mandatory | React dashboard build |
| Flutter SDK | Mandatory (if mobile app is in scope) | Citizen app |
| GPU | Recommended | Speeds up LSTM/GRU/Transformer training; not strictly mandatory for a small ward-level dataset trained on CPU, but recommended if the dataset/sequence length grows |
| Cloud hosting (Render, Netlify) | Mandatory | Deployment |
| Firebase project | Mandatory (if citizen alerts are in scope) | Push notifications |
| Real or synthetic dataset | Mandatory | Blocks everything — see Phase 1 |
| GIS ward-boundary data | Recommended | For Phase 10; MVP can proceed without it |
| LP/MILP solver (PuLP/OR-Tools) | Optional | Only for Advanced supply-plan optimization |
| Model experiment tracking tool | Recommended | e.g., MLflow, for managing 4 models × 3 horizons |
| CI/CD tooling (GitHub Actions) | Recommended | Automates testing/deployment |
| Monitoring/error-tracking tool | Optional (MVP) / Recommended (production) | e.g., Sentry |

---

## 15. Risk Register

| Risk | Probability | Impact | Mitigation | Contingency |
|---|---|---|---|---|
| No real ward-level dataset available | High | Critical | Attempt open-data/government sourcing first; design a calibrated synthetic-data generator as fallback | Ship as clearly-labeled proof-of-concept on synthetic data; revisit with real data later |
| Uncalibrated WAR thresholds mislead stress classification | Medium | High | Keep thresholds configurable, not hardcoded; flag as provisional | Validate/recalibrate with municipal stakeholders before any production use |
| DL models (LSTM/GRU/Transformer) underperform or overfit on small dataset | Medium | Medium | Always benchmark against naive baseline + XGBoost | Report underperformance as a valid finding; ship XGBoost as production model if it wins |
| Ward-level GIS boundary data unavailable | Medium | Low-Medium | Research public GIS sources early (parallel task) | Use simplified/illustrative ward polygons, clearly labeled |
| Leakage-risk labels unavailable | High | Low (supporting module only) | Start with unsupervised anomaly detection (Isolation Forest) | Defer supervised leakage classification to Future scope |
| LP/MILP optimization scope creep | Medium | Medium | Explicitly scope as Advanced/Future, not MVP | Ship rule-based allocator for MVP/Advanced launch |
| Free-tier hosting limitations (cold starts, resource caps) | Medium | Medium | Treat as pilot/demo deployment target | Plan migration path to dedicated infra if project scales |
| Security gaps from adding auth late | Low (if built into Phase 6) | High | Build JWT/RBAC into Phase 6 from day one | Dedicated Phase 14 audit before any deployment |
| Scope creep across MVP/Advanced/Future | Medium | Medium | Strict adherence to Section 7 scope boundaries | Re-prioritize backlog (Phase 17) only after MVP ships |
| No deadline/timeline defined | High | Medium (planning risk) | Flag explicitly in Section 13 | Obtain real deadline/team constraints before committing to sprint planning |

---

## 16. Requirements Traceability

| Requirement | Architecture Component | Implementation Task | Test Case | Deliverable |
|---|---|---|---|---|
| FR1 (data ingestion/merge) | Data Sources → Preprocessing | Phase 1–2 tasks | Integration test: merged dataset row/key integrity | Clean merged dataset |
| FR2 (train & select best model) | Model Training → Validation/Selection | Phase 4–5 tasks | AI/ML test: comparison table populated, beats baseline | Comparison table + selected model |
| FR3 (1/3/7-day forecasts) | Prediction | Phase 4–6 tasks | AI/ML + API test: `/api/forecast` returns 3 horizons | Working forecast endpoint |
| FR4 (reservoir storage %/availability) | Reservoir Availability Analysis | Phase 7 tasks | Unit test: storage % formula | `/api/reservoir` + stress inputs |
| FR5 (demand–supply gap/WAR) | Demand–Supply Analysis | Phase 7 tasks | Unit test: worked example (500/450 ML) | Gap/WAR values in `WaterStress` table |
| FR6 (stress classification) | Water Stress Analysis | Phase 7 tasks | Unit test: threshold boundaries | `/api/water-stress` |
| FR7 (supply plan/alerts) | Smart Supply Plan | Phase 8 tasks | Integration test: allocation respects available water | `/api/supply-plan` |
| FR8 (authenticated REST APIs) | Backend/API layer | Phase 6, 14 tasks | Security test: RBAC/auth enforcement | Secured FastAPI service |
| FR9 (admin dashboard visualization) | System Outputs — Admin Dashboard | Phase 9 tasks | Frontend + E2E test | Deployed React dashboard |
| FR10 (citizen schedule/alerts/complaints) | System Outputs — Citizen App | Phase 11 tasks | E2E test: citizen journey | Deployed Flutter app |
| FR11 (leakage/anomaly detection) | Leakage/Wastage (supporting) | Phase 12 tasks | AI/ML test: anomaly flags on known outliers | `/api/leakage-risk` |

---

## 17. Change Log

| Date | Change | Reason | Impact |
|---|---|---|---|
| Initial version | Created this Implementation Plan from first review of `Project_Overview.md`, `WaterSphere_AI_Project_Complete_Development_Context.pdf`, and `Architecture.jpeg`. | No prior implementation plan or `docs/` folder existed in the workspace. | Establishes the baseline roadmap; all future changes should be appended below, not overwritten. |

---

## 18. Final Quality Check

> Reconciled with the repository on **2026-10-25**. The original checklist is kept with
> its resolved answers; where it once reported an empty workspace, the current state is
> recorded inline.

- [x] Entire relevant `docs/` folder reviewed — **now exists** (`Docs/`, 15 files); all provided files reviewed.
- [x] Architecture reviewed (Architecture.jpeg, PDF §5/§26) and implemented (`Docs/Architecture.md`)
- [x] Research reviewed (PDF full document)
- [x] Project overview reviewed (Project_Overview.md)
- [x] Existing source code reviewed — **exists now**: `backend/`, `frontend/`, `scripts/`, `models/`, 11-table DB
- [x] Requirements identified (Section 1)
- [x] Requirements mapped to implementation (Section 16)
- [x] Architecture mapped to implementation (Section 3)
- [x] Technology stack defined (Section 4) — implemented (FastAPI, PostgreSQL, React/Vite, plain CSS, TF/Keras)
- [x] AI/ML pipeline defined (Section 5) — implemented; 12 models trained, registry + per-horizon selection live
- [x] Database defined (Phase 6, Section 3) — implemented, Alembic head `c8f2a6b1e4d9`
- [x] Backend defined (Phase 6) — implemented, 22 API operations
- [x] Frontend defined (Phase 9) — implemented, light municipal theme + public landing
- [x] APIs defined (Section 1.12, Phase 6) — live OpenAPI at `/openapi.json`
- [x] Integration defined (Phase 13, Section 9) — 38/38 live e2e checks pass
- [x] Testing defined (Section 10) — implemented: 28/28 pytest, 38/38 e2e, CI green (no FE unit tests yet)
- [x] Deployment defined (Section 11) — plan ready; Phase 15 staging not yet executed
- [x] Security considered (Section 1.14, Phase 14) — implemented: JWT + ward-scoped RBAC, upload validation, rate limits
- [x] Dependencies identified (Section 9)
- [x] Risks identified (Section 15)
- [x] MVP defined (Section 7)
- [x] Advanced scope separated (Section 7)
- [x] Research gaps identified (Section 6)
- [x] Open decisions identified (Section 20)
- [x] Timeline included, flagged as `TBD` (Section 13)
- [x] Resource requirements included (Section 14)
- [x] Change log included (Section 17)
- [x] No unsupported assumptions presented as confirmed facts — all uncertain items marked `TBD` / `Research Required` / `Decision Required`

---

## 19. Open Decisions Requiring Human Input

Resolved decisions are struck through with the outcome; genuinely open items remain plain.

1. ~~**Dataset source**~~ → **BMC Mumbai, 24 wards, daily 2023-01-01 → 2025-12-31** (bmc-v1); synthetic-v1 superseded.
2. ~~**WAR thresholds**~~ → provisional config: Safe ≥ 1.0, Moderate 0.85–1.0, High 0.70–0.85, Shortage < 0.70 (env-configurable, pending municipal sign-off).
3. ~~**Model output structure**~~ → separate model per horizon (12 total), selected on validation RMSE.
4. ~~**Transformer inclusion**~~ → included in the comparison; it lost on 3d/7d, so GRU was selected there.
5. ~~**Supply-plan approach**~~ → rule-based engine is the default; LP (PuLP/CBC) available via `SUPPLY_OPTIMIZER`.
6. ~~**Leakage-risk labels**~~ → unsupervised `IsolationForest` only, pending real labels.
7. ~~**Deep-learning framework**~~ → TensorFlow/Keras (TF-CPU container).
8. **Hosting/DB provider specifics** — exact Render/Netlify tiers, managed Postgres provider. *(open)*
9. **Ward-level GIS boundary data source** — approximate polygons ship today. *(open)*
10. **Project deadline / timeline / team size.** *(open)*
11. **Monitoring tooling** — CI exists (GitHub Actions, 3 jobs); Sentry/APM undecided. *(partially open)*
12. ~~**Citizen account model**~~ → open self-registration forced to `citizen`, ward locked at sign-up; admins provisioned. OTP still open.
13. **WAR availability basis** (clarified 2026-10-25) — `EVALUATION.md §5` and `backend/app/inference.py` show the large WAR values come from dividing each reservoir's gross `available_water_ml` (split equally among its serving wards) by forecast demand (range ≈2.9–4000, median ≈184), so every ward reads Safe. Decision needed: keep absolute bands with that framing, or switch to servable-share/net availability. *(open)*
