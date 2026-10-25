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

**Start signed out.** The dashboard opens on the **public landing page** (not the
login form): "Plan the city's water before it runs short.", the Forecast → Stress →
Plan strip, four stat chips fed by `/api/meta` (24 wards, dataset window, model
`bmc-v1`, WAR bands), and two CTAs. Say: *"Officers sign in; a citizen who just
wants to report a leak doesn't need an account."*

Click **Sign in**, use `admin`. Point out the masthead: government strip, ward
selector, date (default `2025-12-31`, i.e. the last day of the dataset — the bounds
come from `/api/meta`, not from code), `bmc-v1` chip, role chip.

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

**Complaints tab.** File a `low-pressure` complaint for Ward C as admin. Point at
the admin extras: **"All wards" filter with per-ward counts**, and the **detail
modal** (reporter, ward, type, status, filed time, address, description, photo).

## 3. Act 3 — The citizen loop (~5 min, the closer)

**3a. Guest report (no account).** Sign out → you're back on the landing page.
Click **"Report a water issue without sign-in."** Fill it in live: full name,
incident ward (from live DB wards), address, incident type — choose **`others`** to
show the inline hint and the taller description prompt — a **mandatory photo**
(JPEG/PNG/WEBP ≤ 5 MB; say that the server sniffs magic bytes, not the filename),
and a description. Submit. Point at the success screen: **a reference number
(`#id`), ward, type and timestamp** — *"that's the whole citizen identity: no
account, no password, no PII beyond what they chose to give."*

**3b. Signed-in citizen.** Sign in page → **"Create a citizen account"** → register
(pick Ward M/E) → auto sign-in. Show: no ward selector (locked chip), **My Supply**
shows only M/E, requesting another ward's data returns 403 (say it — then
optionally prove it via `/docs`). File a complaint as the new citizen.

**3c. Close the loop.** Sign back in as `admin`, open Complaints: both the guest
report and the citizen complaint are there. Filter by the guest's ward to show it
appears, open **View** to show the photo, then **Start work → Resolve**.
*"Full loop: forecast → stress → plan → citizen/guest report → resolution, all
role-scoped."*

## 4. Behind the scenes (if faculty asks)

- **Models:** `data/comparison_table.md` — 4 families × 3 horizons + 2
  baselines. GRU won 3d/7d, xgboost won 1d. Transformer was worst on 3d/7d —
  evidence that attention is unjustified at this data scale.
- **Registry:** `models/manifest.json` — SHA-pinned production artifacts.
- **Verification:** `pytest backend/tests` (**28/28**) + `python3 scripts/e2e_check.py`
  (**38/38**: math asserts, conservation, auth matrix 401/403/404/409, JWT ≈60min,
  login throttling, guest complaint round-trip with photo, `/api/meta`).
- **Design:** light municipal/utility theme in plain CSS (no glows/gradients/blur).
  Stitch project "WaterSphere AI BMC Operations Dashboard" + `Docs/stitch-screens/*.html`
  are the historical visual reference; `Docs/Design_System.md` is the current spec.
- **Docs:** `Docs/EVALUATION.md` (verdict + limits), `Docs/TODO.md` (what's left:
  staging deploy, Flutter app, authoritative GIS).

## 5. Anticipated questions (with answers)

- *"Why is everything Safe?"* → §1 answer: structural surplus in-window; engine proven by unit + scarcity tests.
- *"Why not weather data?"* → Explicitly out of scope per PRD; strongest future accuracy lever.
- *"XGBoost or not?"* → The xgb slot currently runs sklearn HGB (no libomp on the
  training Mac) — API-compatible, documented, rerunnable natively.
- *"Can it scale beyond Mumbai?"* → Schema is ward-based; multi-city scoping is
  a listed P2. WAR bands would need per-city calibration.
- *"Is it secure?"* → JWT + ward-scoped RBAC on every protected endpoint, login
  throttled (10/min/IP), one anonymous write path (guest complaints, 5/min/IP) with
  magic-byte-checked ≤5 MB photos and admin-only photo access, no secrets in code.
  Production still needs a fresh JWT_SECRET, managed DB backups, and a shared
  (Redis) rate-limit store.
- *"Those WAR numbers look wrong"* → Explained in `Docs/EVALUATION.md §5`, not a bug:
  availability is each reservoir's **gross `available_water_ml`, split equally among
  its serving wards**, so WAR runs ~2.9–4000 (median ~184) and every ward classifies
  Safe. Daily yield (4273 MLD vs ≈3300 ML demand) confirms a structural surplus in
  this window. The engine itself is proven by the canonical 500/450 → 0.90 test.
  Open decision: keep absolute bands or switch to servable-share availability.

## 6. Troubleshooting during demo

- Use **`http://localhost:5173`**, not `127.0.0.1` (both work now, localhost is canonical for CORS).
- 7-day forecast slow first time (~30s Keras lazy-load), then fast.
- Rapid re-logins may hit `429` (10/min login throttle) — wait a minute.
- If tabs show errors: `docker compose ps` — both containers must be Up;
  reseed with `docker compose exec api python backend/seed.py`.
