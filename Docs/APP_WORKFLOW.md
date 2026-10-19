# APP_WORKFLOW — WaterSphere AI: what we build, with what, in what order

This is the executable companion to the phase plan: every track, its tools,
its commands, and how the pieces connect. Assumes a macOS/Linux dev machine.

## 0. System map (what talks to what)

```
synthetic/real CSVs ──▶ ML track (scripts/) ──▶ models/*.pkl/*.keras ──┐
                                                                     ├─▶ FastAPI (backend/) ──▶ React dashboard (frontend/)
data/raw/*.csv ──▶ seed ──▶ Postgres ◀─────────────────────────────────┘         └─▶ Flutter app (Phase 11, pending)
```

## 1. Prerequisites (install once)

| Tool | Needed for | Check |
|---|---|---|
| Docker Desktop (daemon running) | Postgres, Linux training + API images | `docker ps` |
| Python 3.11 + pandas/numpy/scikit-learn (host) | Phases 1–3 scripts | `python3 -c "import pandas, sklearn"` |
| Node 22 + npm | Dashboard dev/build | `node --version` |
| Flutter SDK | Phase 11 only | `flutter --version` |

Images we build: `watersphere-ml` (TF-CPU + XGBoost, training), `watersphereai-api`
(FastAPI stack, via `docker compose build api` — plain `up` never rebuilds).

## 2. Track A — ML pipeline (scripts/ + data/ + models/)

Built with: Python, pandas, NumPy, scikit-learn, XGBoost, TensorFlow/Keras (TF-CPU).

| Step | Command (repo root) | Input → Output |
|---|---|---|
| A1 Generate demo data | `python3 scripts/generate_synthetic.py` | seed 42 → `data/raw/` (3655 consumption, 1462 readings, 20 pop rows) |
| A2 Validate any dataset | `python3 scripts/validate_data.py` → must print `PASS` | also the real-data acceptance gate |
| A3 Preprocess + merge | `python3 scripts/preprocess.py` | `data/raw/` → `data/processed/merged_ward_date.csv` (3655) + `data/quality_report.md` |
| A4 Features + splits | `python3 scripts/features.py` | merged → `features.csv` (3470), `train/val/test[.csv,_scaled.csv]`, `split_meta.json` (cuts 2025-05-30/2025-09-11), `scaler.json` (train-fit), `data/eda_report.md` |
| A5 Train (Linux container) | `docker run --rm -v "$PWD:/work" -w /work watersphere-ml python3 scripts/train.py` | splits → `models/xgb+lstm+gru+transformer × 1/3/7d` + `data/validation_metrics.json` |
| A6 Evaluate + select | `docker run --rm -v "$PWD:/work" -w /work watersphere-ml python3 scripts/evaluate.py` | test set (one pass) → `data/comparison_table.md`, `data/test_metrics.json`, `models/active.json` (1d/3d→xgb, 7d→lstm) |

Rules enforced by the scripts: chronological splits (no shuffle), lags/rolls per-ward
with `shift(1)+`, tuning on validation only, test touched once, fixed seeds.

## 3. Track B — Platform (Postgres + FastAPI)

Built with: `postgres:16-alpine`, FastAPI, SQLAlchemy + Alembic (11 tables),
Pydantic v2, JWT (`python-jose`), bcrypt-direct, slowapi (10/min login limit).

| Step | Command | Result |
|---|---|---|
| B1 Start database | `docker compose up -d db` | Postgres on `localhost:5433`, healthy |
| B2 Build API image | `docker compose build api` | `watersphereai-api` with `backend/requirements.txt` |
| B3 Migrate | `docker compose run --rm api alembic upgrade head` | 11 tables (`7f11edf3bbf1`) |
| B4 Seed | `docker compose exec api python backend/seed.py` | bmc-v1: 24 wards, 26304 consumption rows, 7672 readings, admin + citizen_w1 |
| B5 Serve | `docker compose up -d api` | API on `localhost:8000`, xgb loaded at startup, keras lazily |
| B5b Serve (host-direct, Docker down) | `WS_BASE=$PWD DATABASE_URL=postgresql+psycopg2://<user>@localhost:5432/watersphere PYTHONPATH=$PWD/backend .venv/bin/python -m uvicorn app.main:app --port 8000` | Same API without Docker; `WS_BASE` required (code defaults to `/code`) |
| B6 Configure | `.env` (from `.env.example`): `JWT_SECRET`, `WAR_SAFE/MODERATE/HIGH`, `SUPPLY_RESERVE_PCT=0.05`, `CORS_ORIGINS` | thresholds/reserve change without code edits |

Key endpoints: `/api/auth/*`, `/api/forecast?ward_id&target_date&horizon`,
`/api/water-stress?ward_id&date`, `/api/supply-plan?date`, `/api/gis?date`,
`/api/leakage-risk`, `/api/maintenance`, `/api/complaints`, `/api/{population,consumption,reservoir,wards}`.
Interactive contract: `/openapi.json` (or `/docs` in browser).

## 4. Track C — Clients (dashboard now, mobile later)

Dashboard built with: Vite + React 18 + Recharts + axios + Leaflet (`react-leaflet@4`)
+ plain-CSS design tokens. One global ward/date context drives all tabs; citizens
see Forecasts / Stress / My Supply / Complaints only.

| Step | Command (`frontend/`) | Result |
|---|---|---|
| C1 Develop | `npm install` once, then `npm run dev` | http://localhost:5173 (API at `VITE_API_URL`, default :8000) |
| C2 Ship | `npm run build` → `dist/` | must print `✓ built`; deploy `dist/` to Netlify with `VITE_API_URL` set |

Phase 11 (pending): Flutter app consuming the same REST API + Firebase Cloud
Messaging for shortage alerts; APK/internal track for demo.

## 5. Track D — Verify (run after every change)

| Step | Command | Gate |
|---|---|---|
| D1 Unit tests | `docker compose exec api bash -c "pip install -q pytest; PYTHONPATH=/code/backend python -m pytest backend/tests -q"` | 16 passed (11 core + 5 LP) |
| D2 End-to-end + security | `python3 scripts/e2e_check.py` (host, stdlib only) | 31/31: full admin→citizen journey, stress/plan math asserts, auth matrix 401/403/404/409, JWT ≈60min, login 429 |
| D2b Drift guard | `docker compose exec -T api python - < scripts/drift_check.py` | exit 0 healthy / 1 drifted (monthly cron) |
| D2c Backup | `sh scripts/backup_db.sh [dir]` | pg_dump snapshot under `backups/` |
| D3 Frontend | `cd frontend && npm run build` + browser click-through | build PASS, zero console errors |

## 6. Track E — Real-data swap (friends deliver)

1. Drop real CSVs into `data/raw/` matching `data/data_dictionary.md` (same columns, units ML, `Ward_ID + Date` keys).
2. `python3 scripts/validate_data.py` → PASS (else fix grain/gaps with friends).
3. Re-run A3 → A6 (retrain in container, re-select in `models/active.json`).
4. Recalibrate WAR env bands (P0-2), re-seed DB (`backend/seed.py`), re-run D1–D3.
5. No code changes expected — pipeline is source-agnostic by design.

## 7. Track F — Deploy (Phase 15, when accounts are ready)

Render: API service (Docker, `Dockerfile.api` + `--build`) + managed Postgres;
set `DATABASE_URL`, fresh `JWT_SECRET`, `CORS_ORIGINS=https://<netlify-site>`;
run `alembic upgrade head`, seed once, point `scripts/e2e_check.py` at staging.
Netlify: build `frontend/` with `VITE_API_URL=https://<render-api>`.
