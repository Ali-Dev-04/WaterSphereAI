# WaterSphere AI — Live Demo Script (bmc-v1)

Showcase the full working system to teammates and faculty. Total: ~20 minutes.
Everything below is live — no slides, no mocks.

## 0. Before you start (2 min, one time)

```sh
cd "WaterSphere AI"
docker compose up -d db api     # Postgres :5433, API :8000
cd frontend && npm run dev       # dashboard http://localhost:5173
```

Open two browser windows: **http://localhost:5173** (dashboard) and
**http://localhost:8000/docs** (interactive API contract).

Accounts (type them in — no hints on screen by design):

| Role | Username | Password | Sees |
|---|---|---|---|
| Admin (planner) | `admin` | `admin123` | All 24 wards, everything |
| Citizen (Ward A) | `citizen_w1` | `citizen123` | Own ward only |
| New citizen | sign up on the login page | — | Whichever ward you pick |

Dataset: **BMC Mumbai, 24 wards (A–T), daily 2023–2025** — 26,304 consumption
rows, 7 reservoirs (Bhatsa 976 MCM … Vihar 9.2 MCM). Labeled `bmc-v1`
everywhere in the UI.

## 1. Act 1 — The planner's morning (admin, ~8 min)

Sign in as `admin`. Point out the masthead: ward selector, date
(default 2025-12-20), `bmc-v1` chip, role chip.

**Forecasts tab.** Three cards: 1-day (xgboost), 3-day (gru), 7-day (gru),
each with test accuracy (MAPE ≈ 3.2–3.4%, R² ≥ 0.990). Below: 45-day actual
demand with forecast dots. Say: *"Three horizons, best-model-per-horizon,
selected on validation RMSE — never on the test set."*

**Water Stress tab.** Ward detail card: WAR bar with threshold ticks,
`WAR = available ÷ forecast`, gap in ML. Then the all-wards table with
status pills. State the honest finding: *"On this 2023–2025 window every ward
reads Safe — total daily yield (4273 MLD) structurally exceeds demand. That is
a dataset fact, documented in Docs/EVALUATION.md §5, not an engine failure —
the engine reproduces the canonical 500/450 → WAR 0.90 Moderate exactly."*

**Supply Plan tab.** Reservoir pools with utilization bars, ward allocation
table with total footer. *"Severity-weighted, never over-allocates — pools
are conserved exactly, asserted live by the test suite. An LP-optimal
(PuLP/CBC) engine ships beside the rule engine via SUPPLY_OPTIMIZER."*
Click **Export CSV** to download `supply-plan-{date}.csv` (ward rows + pool
summary) — the artifact a manager carries into a review meeting.

**GIS Map tab.** Mumbai-centered stress choropleth + 7 reservoir markers with
popups. Caveat on screen: polygons are approximate centroid boxes.
*Demo tip:* live wards are all Safe, so walk faculty through the **category
key strip** under the map (all four pills + WAR ranges), then prove the other
states classify correctly with `docker compose exec api bash -c
"PYTHONPATH=/code/backend python -m pytest backend/tests/test_stress.py -q"`
— the 500/450 → Moderate boundary test is the engine's proof.

## 2. Act 2 — Operations depth (~5 min)

**Reservoirs tab.** 7-source dropdown, KPI strip (storage %, available ML,
60-day range), dual-axis chart, comparison table with capacity total.

**Leakage tab.** *"Loss = supplied − consumed (~11%)."* Anomaly flags from an
IsolationForest screen (unsupervised — say so explicitly), plus the BMC
maintenance register (123 incidents). Supervised classification is listed as
future work pending labeled data — good faculty honesty point.

**Complaints tab.** File a `low-pressure` complaint for Ward C as admin.

## 3. Act 3 — The citizen loop (~5 min, the closer)

Sign out → **"Create a citizen account"** → register (pick Ward M/E) → auto
sign-in. Show: no ward selector (locked chip), **My Supply** shows only M/E,
requesting another ward's data returns 403 (say it — then optionally prove it
via `/docs`). File a complaint as the new citizen. Sign back in as `admin`:
the complaint is there — **Start work → Resolve**. *"Full loop: forecast →
stress → plan → citizen alert → complaint → resolution, all role-scoped."*

## 4. Behind the scenes (if faculty asks)

- **Models:** `data/comparison_table.md` — 4 families × 3 horizons + 2
  baselines. GRU won 3d/7d, xgboost won 1d. Transformer was worst on 3d/7d —
  evidence that attention is unjustified at this data scale.
- **Registry:** `models/manifest.json` — SHA-pinned production artifacts.
- **Verification:** `pytest backend/tests` (16/16) + `python3 scripts/e2e_check.py`
  (31/31: math asserts, conservation, auth matrix 401/403/404/409, JWT ≈60min,
  login throttling).
- **Design:** Stitch project "WaterSphere AI BMC Operations Dashboard"
  (10 screens) + `Docs/stitch-screens/*.html` reference for the React port.
- **Docs:** `Docs/EVALUATION.md` (verdict + limits), `Docs/TODO.md` (what's left:
  staging deploy, Flutter app, authoritative GIS).

## 5. Anticipated questions (with answers)

- *"Why is everything Safe?"* → §1 answer: structural surplus in-window; engine proven by unit + scarcity tests.
- *"Why not weather data?"* → Explicitly out of scope per PRD; strongest future accuracy lever.
- *"XGBoost or not?"* → The xgb slot currently runs sklearn HGB (no libomp on the
  training Mac) — API-compatible, documented, rerunnable natively.
- *"Can it scale beyond Mumbai?"* → Schema is ward-based; multi-city scoping is
  a listed P2. WAR bands would need per-city calibration.
- *"Is it secure?"* → JWT + ward-scoped RBAC on every endpoint, admin
  provisioning only (self-reg forced to citizen), login throttled, no secrets
  in code. Production still needs a fresh JWT_SECRET + managed DB backups.

## 6. Troubleshooting during demo

- Use **`http://localhost:5173`**, not `127.0.0.1` (both work now, localhost is canonical for CORS).
- 7-day forecast slow first time (~30s Keras lazy-load), then fast.
- Rapid re-logins may hit `429` (10/min login throttle) — wait a minute.
- If tabs show errors: `docker compose ps` — both containers must be Up;
  reseed with `docker compose exec api python backend/seed.py`.
