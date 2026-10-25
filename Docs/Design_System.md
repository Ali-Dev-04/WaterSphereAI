# Design_System.md — WaterSphere AI

Applies to React admin dashboard and Flutter citizen app. Goal: one visual language across both, legible to municipal staff and citizens.

## 1. Principles
- Data-first: forecasts, stress, and plans must be readable in <5s.
- Geographic thinking: every ward-level number links to the map where possible.
- Trust: provisional values (synthetic data, uncalibrated thresholds) are always labeled as such.

## 2. Colors (implemented tokens — `frontend/src/styles.css`)
| Token | Value | Use |
|---|---|---|
| `--ws-deep` | `#0B3D62` | Government strip, login brand panel |
| `--ws-primary` | `#0B5FA5` | Primary buttons, links, active tab, accents |
| `--ws-primary-soft` | `#E8F1F8` | Chips, guest hints, subtle fills |
| `--ws-accent` | `#147CB5` | Chart lines (actual demand / storage) |
| `--ws-bg` | `#F4F6F9` | App background |
| `--ws-surface` | `#FFFFFF` | Cards, panels, tables |
| `--ws-border` | `#DBE2EA` | Dividers, card borders |
| `--ws-text` / `--ws-muted` | `#16283A` / `#5C6B7A` | Text / secondary text |
| Stress Safe | `#14804A` bg `#E7F5EC` | WAR band + badge |
| Stress Moderate | `#8A6400` bg `#FBF3D9` | — |
| Stress High | `#B45009` bg `#FCEFE2` | — |
| Stress Shortage | `#B42318` bg `#FCEBE9` | — |

**Visual language (locked 2026-10-25):** light municipal/utility. No glows, no decorative gradients, no backdrop-blur, no neon. Borders + 1px shadows carry hierarchy; water-blue is the only accent. Stress colors must match GIS choropleth + dashboard badges exactly. Never use red/green alone to convey stress — always pair with label text + dot.

## 3. Typography
- Dashboard (React): Inter (system fallback). Landing hero 44/50, login hero 23/30, app title 17, section headings 14 uppercase tracked, body 13–14/21, caption 11–12/16.
- Citizen app (Flutter): Roboto (Android) / SF (iOS) via platform default; same size ramp.
- Numbers: tabular-nums for all ML values, ML units always shown (`ML`, `WAR 0.90`, `MAPE 8.2%`).

## 4. Spacing / Layout
- 8px base grid. Card radius 10px, padding 16–24px. Page max-width 1280px dashboard.
- Signed-out entry is a **public landing page** (hero + 3 steps + meta stat chips + CTAs), then a split login card (brand panel | form).
- Dashboard layout: government strip → masthead → ward/date context bar → **horizontal tab nav** (Forecasts, Water Stress, Supply Plan, GIS Map, Leakage, Reservoirs, Complaints) → cards. (Top tabs replaced the earlier left-nav idea.)
- Mobile: bottom nav planned for Flutter (Schedule, Alerts, Complaints, Account); dashboard collapses to single-column cards with horizontally scrollable tables.

## 5. Components
- **Landing hero:** objective statement, two CTAs (Officer/citizen sign-in · Report without sign-in), live stat chips from `/api/meta`, Forecast/Stress/Plan explainer strip.
- **Sign-in card:** brand panel (mission, capabilities, model chip) + form; **"Report a complaint without sign-in" is a full-width secondary button under an “or” divider** (never a text link). Registration mode locks the ward; guest mode renders the report form.
- **Guest complaint form:** full name, incident ward (live `/api/public/wards`), mandatory address, incident type (`no-supply`, `low-pressure`, `leakage`, `quality`, `billing`, **`others`**), **mandatory photo** (JPEG/PNG/WEBP ≤5 MB), mandatory description. `others` shows an explain-in-detail hint and requires ≥25 chars. Success screen shows the reference number `#id`.
- **Ward selector + date picker:** global, persists across tabs; date bounds and default come from `/api/meta.window`, not constants.
- **Forecast chart:** line chart (actual vs. predicted) per horizon tabs [1-day|3-day|7-day]; tooltip shows value + model version; light grid `#E8EDF2`, line `#147CB5`.
- **Stress badge:** colored pill + label + WAR value. **WAR scale:** four-band bar with threshold ticks; label explains gap calculation.
- **Supply plan table:** ward rows, allocated ML, gap, alert icon for High/Shortage; CSV export.
- **Map (Leaflet web):** native light OSM tiles (no dark filter), ward polygons colored by stress, reservoir markers with popup (storage %, available ML), category key strip with all four bands.
- **Complaints:** status pills (Filed → In-progress → Resolved); admin "All wards" filter with per-ward counts; detail modal with reporter, ward, timestamps, address, description and authorized photo preview.
- **Empty/loading/error:** skeleton cards for charts; explicit "no data" state; inline error cards, never blank.

## 6. Charts / Data-viz Rules
- Always show horizon, model name/version, and data provenance (real vs. synthetic) near forecasts.
- Y-axis starts at 0 for ML; WAR axis fixed 0–1.2 with threshold bands drawn.
- No 3D, no truncated axes.

## 7. Accessibility / i18n
- Contrast ≥4.5:1 for text. All form inputs labeled. Keyboard-navigable dashboard. Touch targets ≥44px in app.
- Citizen app strings externalized for future regional-language support; dates/numbers locale-formatted.

## 8. CSS Framework Decision (closed 2026-09-26)
Plain CSS with design tokens in `frontend/src/styles.css` — no Tailwind/MUI. This keeps the municipal theme explicit and dependency-free; charts use Recharts, the map uses react-leaflet + OSM tiles.
