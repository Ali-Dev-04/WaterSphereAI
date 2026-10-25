# TODO — WaterSphere AI: remaining work + improvements

Status date: 2026-10-25 (code complete through Phase 14; guest complaints + landing + light UI shipped; only deploy / Flutter remain). Source of truth for progress: `Context.md`.
Legend: ✅ done · 🔲 remaining · 💡 improvement (not in original plan).

## 1. Phase completion checklist

| Phase | Status | Remaining items |
|---|---|---|
| 1 Dataset (bmc-v1) | ✅ converted + PASS (24 wards, 26304 rows, 7 reservoirs) | `level_m` placeholder, serving map synthetic assignment, D7 not ingested |
| 2 Preprocessing | ✅ re-ran on bmc-v1 | — |
| 3 Features + splits | ✅ re-ran (train 17784/val 3816/test 3816) | — |
| 4 Training (12 models) | ✅ BMC done (host TF 2.16 CPU; xgb slot = HGB fallback, libomp missing) | — |
| 5 Evaluation + selection | ✅ bmc-v1 (1d xgb, 3d/7d gru; test MAPE 3.2–3.4%, R² ≥0.990) | — |
| 6 DB + Backend/API | ✅ re-seeded bmc-v1 live (24 wards, 26304 rows, 7672 readings) | — |
| 7 Water stress engine | ✅ | — |
| 8 Supply planner (rule-based) | ✅ | — |
| 9 Admin dashboard MVP | ✅ (BMC data + live click-through 2026-10-25: public landing, light municipal theme, meta-driven ward/date/WAR copy; mobile-width sweep still open) | Mobile-width visual sweep (360/768) on a real device |
| 10 GIS module | ✅ | Authoritative ward boundaries (currently approximate grid) |
| 11 Citizen app (Flutter) | 🔲 DEFERRED by user | Full scope below |
| 12 Leakage + complaints | ✅ (unsupervised only) + guest reports without sign-in (reference #, mandatory photo, admin ward filter + photo modal) | Supervised classification needs real labels |
| 13 Integration + E2E | ✅ re-verified 2026-10-25 live (**pytest 28/28 + e2e 38/38**; CI green on `160bb8b`) | Re-run after every future change |
| 14 Security hardening | ✅ | See §3 residual items |
| 15 Deployment | 🔲 NOT STARTED | See §2 |
| 16 Documentation + evaluation | ✅ (`Docs/EVALUATION.md` + registry manifest + current Context) | API reference auto-served via OpenAPI |
| 17 Future enhancements | 🔲 BACKLOG | See §4 |

## 2. Remaining for a complete project (P0 — must do to call it done)

- [x] **P0-1 Real-v1 data swap (DONE 2026-10-05).** Convert + PASS + Phases 2–5 retrained/re-selected (1d xgb, 3d/7d gru; MAPE 3.2–3.4%) + DB re-seeded + e2e suite green at the time (**31/31 then; 38/38 now**). Residual caveats: `level_m` placeholder, hardcoded serving map, D7 not ingested, centroid-box GIS, HGB-in-xgb-slot.
- [x] **P0-2 WAR threshold calibration (DONE 2026-10-05).** Empirical analysis (`war_calibrate.py`): structural surplus in-window, absolute bands kept + explicit in `.env`/compose, canonical example green. Municipal sign-off still required before production use.
- [ ] **P0-3 Phase 11 citizen app.** Flutter: auth (citizen role), ward supply schedule (from `/api/supply-plan`, filtered), shortage alert banner (from `alert` flags), complaint file/track (`/api/complaints`), FCM push wiring (Firebase project + `google-services.json`, never committed). Demo distribution via APK/internal track.
- [ ] **P0-4 Phase 15 staging deploy.** Render (API + managed Postgres) + Netlify (dashboard `dist/`, `VITE_API_URL` pointed at Render). Runbook: env vars (`DATABASE_URL`, `JWT_SECRET` — fresh strong secret, `CORS_ORIGINS` = Netlify URL), `alembic upgrade head` on deploy, seed once, smoke `scripts/e2e_check.py` against staging URL.
- [x] **P0-5 Dashboard browser click-through (desktop DONE 2026-10-25).** Sign-out → landing → sign-in → all tabs render (light theme), guest complaint submitted with photo (ref #3) and seen by admin under its ward filter, complaint modal photo fetches. Remaining: mobile-width sweep (360px/768px).
- [x] **P0-6 Phase 16 evaluation report (DONE 2026-10-05).** `Docs/EVALUATION.md`: comparison tables, selection rationale, transformer verdict, WAR calibration, retraining policy, limitations.

## 3. Security/robustness residuals (P1 — do before any shared staging)

- [x] Production `JWT_SECRET` checklist item remains deploy-scope; dev `.env` never committed. Seeded dev passwords still `admin123`/`citizen123` (rotate before sharing).
- [ ] Postgres backups (managed-provider snapshots) + tested restore; `pgdata` volume is currently the only copy.
- [x] Demo credential hints removed from login page (2026-10-05). Credentials live only in `Docs/demo.md` (presenter cheat sheet).
- [x] Citizen account model decided (self-reg, forced `citizen`, ward locked; admins provisioned). OTP still undecided — acceptable for local pilot.
- [x] Guest complaint abuse surface (2026-10-25): `POST /api/complaints/public` is the only unauthenticated write, 5/min/IP via slowapi, DB-validated ward, length bounds, magic-byte image sniffing, 5 MB cap, UUID filenames, admin-only `GET /api/complaints/{cid}/photo` with path-traversal guard.
- [ ] Rate limits are **in-process/in-memory** (slowapi default) — reset on restart and per worker; move to Redis before any public deployment.
- [x] API pagination/caps audit (2026-10-05). Large tables capped (consumption/readings 5000, complaints 500, maintenance 200); population capped 5000; wards/reservoirs/GIS bounded by domain (≤ dozens). City-scale revisit still noted.
- [x] Dependency vulnerability scan (2026-10-05). `npm audit` 0 vulns. `pip-audit`: 1 finding (ecdsa 0.19.2, PYSEC-2026-1325, no upstream fix) — ACCEPTED residual: HS256-only JWT (`config.py:14`), ecdsa code path unreachable. Revisit if jose usage changes.

## 4. High-impact improvements (P1–P2 — biggest project impact first)

- [x] 💡 **P1 LP/MILP allocator (DONE 2026-10-05).** `backend/app/planner_lp.py` (PuLP/CBC, max severity-weighted met demand, same contract as rule engine) + 5 unit tests + `SUPPLY_OPTIMIZER` env flag (default `rule`). Suite green at the time (16/16 pytest, 31/31 e2e); current baseline is **28/28 pytest, 38/38 e2e**.
- [x] 💡 **P1 Automated retraining guard (DONE 2026-10-05).** `scripts/drift_check.py` (live MAPE vs manifest, exit 1 on drift, cron-ready monthly). Full cron install is deploy scope.
- [x] 💡 **Backups (local DONE).** `scripts/backup_db.sh` (pg_dump, verified). Managed snapshots are deploy scope.
- [x] 💡 **P1 Model registry (lightweight DONE).** `scripts/registry.py` → versioned `models/manifest.json` (SHA-pinned artifacts + metrics per retrain). MLflow remains optional.
- [ ] 💡 **P2 Supervised leakage classification.** Needs labeled incident↔reading pairs from the municipality (currently 123 BMC incidents, unlabeled). Random Forest/XGBoost risk scores per ward. Impact: turns leakage from flags into prioritized repair lists.
- [x] 💡 **P2 CI (basic) DONE.** GitHub Actions on every push: backend pytest (28 tests), ml-smoke, frontend build — green on `160bb8b`; `httpx2` test dep pinned. Remaining: e2e against an ephemeral Postgres service + auto-deploy staging.
- [ ] 💡 **P2 Observability.** Sentry (API) + structured forecast-error logging vs realized consumption (feedback loop for retraining trigger).
- [ ] 💡 **P2 Multi-ward/city support.** `city_id` scoping in schema + per-city WAR calibration. Impact: product scales beyond pilot.
- [ ] 💡 **P3 Weather integration.** Explicitly out of current scope, but rainfall is the strongest exogenous demand driver — highest-accuracy lever if rescoped later.
- [ ] 💡 **P3 Accessibility + i18n.** Contrast/keyboard audit, regional-language strings in citizen app.
- [ ] 💡 **P3 Authoritative GIS.** Replace approximate grid with municipal GeoJSON; add density/demand choropleth layers.
- [ ] 💡 **P1 Decide the availability basis for WAR (clarified 2026-10-25).** `/api/gis` + `/api/water-stress` report `war` values ~10²–10³ (ward A 4080.458) because the engine divides each reservoir's **gross `available_water_ml`, split equally among its serving wards**, by forecast demand — `Docs/EVALUATION.md §5` documents the range ≈2.9–4000, median ≈184, so all wards classify Safe. Not an engine bug (canonical 500/450 → 0.90 passes). Owner decision: keep absolute bands + document the framing, or switch to servable-share / net-availability so the WAR gauge is demo-meaningful.

## 5. Suggested build order from here

1. Resolve the WAR units anomaly (P1) so the stress gauge is trustworthy for demos.
2. P0-4 staging deploy (with §3 security residuals first: fresh JWT secret, backups, Redis-backed limits).
3. P0-3 Flutter app.
4. Mobile-width visual sweep + accessibility pass. P2/P3 as time permits.
