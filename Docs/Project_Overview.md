Project Overview
Project Title:
AI-Powered Smart Water Management Platform for Intelligent Water Supply Planning and Leakage Risk Prediction
This project is an AI-based water management system designed to help municipal authorities plan urban water supply more intelligently.
The system uses population, population density, historical water consumption, reservoir data, and time/seasonal information to predict how much water will be required in the future.
First, the collected data is cleaned and processed. Different machine-learning and deep-learning models such as XGBoost, LSTM, GRU, and Transformer are trained and compared to forecast future water demand for 1-day, 3-day, and 7-day periods.
After forecasting demand, the system checks the available water in reservoirs and compares it with the expected demand. Based on this comparison, it identifies the level of water stress, such as safe, moderate, high-risk, or shortage conditions.
Finally, the platform generates smart water-supply recommendations, such as zone-wise allocation and shortage alerts. The results can be displayed through an admin dashboard, GIS visualization, and citizen application.
---

## Current implementation state (2026-10-25)

This is no longer a concept document — the platform is built and running locally.

- **Data:** BMC Mumbai, **24 wards**, daily **2023-01-01 → 2025-12-31** (26,304 consumption rows, 7,672 reservoir readings, 7 reservoirs), validated by `scripts/validate_data.py`.
- **Models:** 4 families (XGBoost/HGB, LSTM, GRU, Transformer) × 3 horizons (1/3/7 days), selected on validation RMSE per horizon; held-out test MAPE ≈ 3.2–3.4%, R² ≥ 0.990. Registry `models/manifest.json`, active selection in `models/active.json`.
- **Backend:** FastAPI + PostgreSQL (11 tables, Alembic head `c8f2a6b1e4d9`), JWT auth with ward-scoped RBAC, 22 API operations including demand forecasting, WAR stress, supply planning (rule + optional LP), GIS choropleth, leakage risk, maintenance and complaints.
- **Complaints:** citizens file and track their own; admins file for any ward, change status, and view photos. Guests can report **without an account** from the public site with a mandatory JPEG/PNG/WEBP photo (≤5 MB) and receive a reference number.
- **Frontend:** React 18 + Vite dashboard with a public landing page, sign-in/registration/guest-report card, and role-aware tabs (Forecasts, Water Stress, Supply Plan, GIS, Leakage, Reservoirs, Complaints). All user-visible configuration comes from `GET /api/meta`; styling is a light municipal/utility theme in plain CSS.
- **Verification:** `pytest backend/tests` **28/28**, `scripts/e2e_check.py` **38/38**, `npm run build` PASS, CI green on the frontend/backend/ml-smoke jobs.
- **Remaining:** staging deploy, Flutter citizen app, authoritative ward boundaries, and an owner decision on a WAR available-water unit anomaly (see `Docs/TODO.md`).

Read `Docs/Context.md` for the authoritative, per-task history.
