# Testing.md — WaterSphere AI

Expands IMPLEMENTATION_PLAN §10. No phase gate passes with red tests.

**Current state (2026-10-25):** backend `pytest` **28/28 passing**, live end-to-end
`scripts/e2e_check.py` **38/38 passing**, frontend build PASS, CI green. There are
**no frontend unit tests yet** and no separate ML test package (ML math is covered by
backend tests + the e2e math asserts).

## 1. Levels + Real Commands

| Level | Scope | Command (actual) | Status |
|---|---|---|---|
| Unit + API (Py) | WAR/stress/supply logic, LP optimizer, leakage screen, guest complaints, auth/RBAC via `TestClient` | `DATABASE_URL=postgresql+psycopg2://<user>@localhost:5432/watersphere PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -q` | ✅ 28 passed |
| Unit (FE) | React components | — (no test runner configured; `npm run build` is the only FE gate) | 🔲 not started |
| Integration / E2E | live API against a seeded Postgres: auth matrix, forecast/stress/plan math, guest complaint round-trip, `/api/meta` | `WS_E2E_BASE=http://localhost:8000 .venv/bin/python scripts/e2e_check.py` | ✅ 38/38 |
| ML validation | schema/range checks, beats baseline, val↔test gap, leakage checks, determinism | `python3 scripts/validate_data.py` + `data/comparison_table.md` review (no `ml/tests` package) | ✅ manual + scripted |
| Frontend build | Vite production build | `cd frontend && npm run build` | ✅ PASS |
| Performance | p95 API latency, inference ms/req | `locust`/k6 smoke (not written) | 🔲 not started |
| Security | bypass, RBAC boundary, injection, secret scan | covered by e2e auth matrix + `Security.md §6` checklist | ✅ automated parts |

`httpx2` is a **test-only** dependency required by Starlette's `TestClient`; it is
installed in CI's backend job alongside `pytest`. CI runs three jobs: `backend`
(pytest, 28 tests), `ml-smoke`, `frontend` (build).

## 2. ML-Specific Gates (must all pass)
- [x] Train/val/test chronological (no shuffle); cuts recorded in `split_meta.json`.
- [x] Tuning on validation only; test set touched once per selection cycle.
- [x] Selected models beat seasonal-naive baselines on 1/3/7-day validation metrics.
- [x] No future leakage: rolling/lag use `shift(1)` minimum; per-ward `groupby`.
- [x] Edge cases covered: sparse-history ward, missing reservoir reading.
- [x] Comparison table (`data/comparison_table.md`) fully populated — 4 families × 3 horizons + 2 baselines.

## 3. API / E2E Assertions (what `e2e_check.py` actually checks)
- Auth matrix on every protected surface: no token 401, tampered token 401, citizen-other-ward 403, admin-only complaint status/photo 403, self-register-as-admin 403, duplicate username 409, unknown ward 404.
- JWT lifetime ≈ 60 minutes; wrong password and unknown user both 401; login throttling produces a 429.
- `/api/meta` is public and returns a DB-derived ward count (24), a valid date window, and the three WAR bands.
- Worked example: forecast 500 ML + available 450 ML → gap 50, WAR 0.90, category per current thresholds.
- Supply plan never allocates more than available (minus reserve %); pools conserve exactly.
- Guest complaint round-trip: `POST /api/complaints/public` with multipart photo → reference id → admin sees it with `has_photo` → `GET /api/complaints/{cid}/photo` returns the original bytes.
- Full journey: `admin login → forecast → stress → plan → citizen complaint → admin status update` with zero manual DB edits.

## 4. Coverage / Quality Bars
- Target: backend services (WAR, allocator, inference) ≥80% line coverage; feature-eng functions 100% on leakage-sensitive paths. **Coverage is not currently measured in CI** — the suite passes on assertions, not a coverage gate.
- `ruff`, `black --check`, `mypy` (py), `eslint`, `dart analyze` clean before merge — **not yet wired into CI**; frontend build is the enforced FE gate.
- Known residual: the WAR **availability basis** (each reservoir's gross `available_water_ml` split equally among its serving wards → values ≈2.9–4000, all-Safe) is a documented calibration decision in `EVALUATION.md §5` and `TODO.md`, not a test failure.

## 5. Data Test Fixtures
Fixtures live under `backend/tests/` (in-memory SQLite/DB-backed fixtures per test) and
`data/quality_report.md` for dataset validation. The canonical WAR worked example
(500/450 → 0.90) lives in `backend/tests/test_stress.py`. Synthetic provenance is
labeled explicitly in the generated CSVs and in `data/eda_report.md`.
