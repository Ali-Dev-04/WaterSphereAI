# TODO — WaterSphere AI: remaining work + improvements

Status date: 2026-10-05 (all local work verified; only deploy / Flutter / click-through remain). Source of truth for progress: `Context.md`.
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
| 9 Admin dashboard MVP | ✅ (BMC fixes 2026-10-05: dynamic reservoirs, Mumbai map center, build PASS; Stitch port phases 1–2: SCADA shell, split login, banners/KPIs/footers/pills, mobile rules) | Browser click-through still pending (no desktop browser in dev session) |
| 10 GIS module | ✅ | Authoritative ward boundaries (currently approximate grid) |
| 11 Citizen app (Flutter) | 🔲 DEFERRED by user | Full scope below |
| 12 Leakage + complaints | ✅ (unsupervised only) | Supervised classification needs real labels |
| 13 Integration + E2E | ✅ re-verified bmc-v1 live (pytest 11/11 + e2e 31/31) | Re-run after every future change |
| 14 Security hardening | ✅ | See §3 residual items |
| 15 Deployment | 🔲 NOT STARTED | See §2 |
| 16 Documentation + evaluation | ✅ (`Docs/EVALUATION.md` + registry manifest + current Context) | API reference auto-served via OpenAPI |
| 17 Future enhancements | 🔲 BACKLOG | See §4 |

## 2. Remaining for a complete project (P0 — must do to call it done)

- [x] **P0-1 Real-v1 data swap (DONE 2026-10-05).** Convert + PASS + Phases 2–5 retrained/re-selected (1d xgb, 3d/7d gru; MAPE 3.2–3.4%) + DB re-seeded + e2e 31/31 live. Residual caveats: `level_m` placeholder, hardcoded serving map, D7 not ingested, centroid-box GIS, HGB-in-xgb-slot.
- [x] **P0-2 WAR threshold calibration (DONE 2026-10-05).** Empirical analysis (`war_calibrate.py`): structural surplus in-window, absolute bands kept + explicit in `.env`/compose, canonical example green. Municipal sign-off still required before production use.
- [ ] **P0-3 Phase 11 citizen app.** Flutter: auth (citizen role), ward supply schedule (from `/api/supply-plan`, filtered), shortage alert banner (from `alert` flags), complaint file/track (`/api/complaints`), FCM push wiring (Firebase project + `google-services.json`, never committed). Demo distribution via APK/internal track.
- [ ] **P0-4 Phase 15 staging deploy.** Render (API + managed Postgres) + Netlify (dashboard `dist/`, `VITE_API_URL` pointed at Render). Runbook: env vars (`DATABASE_URL`, `JWT_SECRET` — fresh strong secret, `CORS_ORIGINS` = Netlify URL), `alembic upgrade head` on deploy, seed once, smoke `scripts/e2e_check.py` against staging URL.
- [ ] **P0-5 Dashboard browser click-through.** Login → each tab incl. GIS map tiles render, no console errors; mobile widths (360px/768px).
- [x] **P0-6 Phase 16 evaluation report (DONE 2026-10-05).** `Docs/EVALUATION.md`: comparison tables, selection rationale, transformer verdict, WAR calibration, retraining policy, limitations.

## 3. Security/robustness residuals (P1 — do before any shared staging)

- [ ] Production `JWT_SECRET` (32+ random bytes) + confirm `.env` never committed; rotate seeded dev passwords.
- [ ] Postgres backups (managed-provider snapshots) + tested restore; `pgdata` volume is currently the only copy.
- [x] Demo credential hints removed from login page (2026-10-05). Credentials live only in `Docs/demo.md` (presenter cheat sheet).
- [ ] Decide citizen account model (self-reg + OTP vs provisioned) — currently open self-reg as citizen (UI shipped Oct-05); OTP still undecided.
- [x] API pagination/caps audit (2026-10-05). Large tables capped (consumption/readings 5000, complaints 500, maintenance 200); population capped 5000; wards/reservoirs/GIS bounded by domain (≤ dozens). City-scale revisit still noted.
- [x] Dependency vulnerability scan (2026-10-05). `npm audit` 0 vulns. `pip-audit`: 1 finding (ecdsa 0.19.2, PYSEC-2026-1325, no upstream fix) — ACCEPTED residual: HS256-only JWT (`config.py:14`), ecdsa code path unreachable. Revisit if jose usage changes.

## 4. High-impact improvements (P1–P2 — biggest project impact first)

- [x] 💡 **P1 LP/MILP allocator (DONE 2026-10-05).** `backend/app/planner_lp.py` (PuLP/CBC, max severity-weighted met demand, same contract as rule engine) + 5 unit tests + `SUPPLY_OPTIMIZER` env flag (default `rule`). pytest 16/16, e2e 31/31.
- [x] 💡 **P1 Automated retraining guard (DONE 2026-10-05).** `scripts/drift_check.py` (live MAPE vs manifest, exit 1 on drift, cron-ready monthly). Full cron install is deploy scope.
- [x] 💡 **Backups (local DONE).** `scripts/backup_db.sh` (pg_dump, verified). Managed snapshots are deploy scope.
- [x] 💡 **P1 Model registry (lightweight DONE).** `scripts/registry.py` → versioned `models/manifest.json` (SHA-pinned artifacts + metrics per retrain). MLflow remains optional.
- [ ] 💡 **P2 Supervised leakage classification.** Needs labeled incident↔reading pairs from the municipality (currently 123 BMC incidents, unlabeled). Random Forest/XGBoost risk scores per ward. Impact: turns leakage from flags into prioritized repair lists.
- [ ] 💡 **P2 CI/CD.** GitHub Actions: pytest + e2e against ephemeral Postgres + frontend build on every push; auto-deploy staging. Impact: catches regressions like the lifespan/slowapi ones automatically.
- [ ] 💡 **P2 Observability.** Sentry (API) + structured forecast-error logging vs realized consumption (feedback loop for retraining trigger).
- [ ] 💡 **P2 Multi-ward/city support.** `city_id` scoping in schema + per-city WAR calibration. Impact: product scales beyond pilot.
- [ ] 💡 **P3 Weather integration.** Explicitly out of current scope, but rainfall is the strongest exogenous demand driver — highest-accuracy lever if rescoped later.
- [ ] 💡 **P3 Accessibility + i18n.** Contrast/keyboard audit, regional-language strings in citizen app.
- [ ] 💡 **P3 Authoritative GIS.** Replace approximate grid with municipal GeoJSON; add density/demand choropleth layers.

## 5. Suggested build order from here

1. P0-5 click-through (user walkthrough in progress) — closes the MVP.
2. P0-3 Flutter app, then P0-4 staging deploy (with §3 security residuals first).
3. P1 LP/MILP + automated retraining cron. P2/P3 as time permits.
