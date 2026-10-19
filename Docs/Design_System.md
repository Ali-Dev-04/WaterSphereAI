# Design_System.md — WaterSphere AI

Applies to React admin dashboard and Flutter citizen app. Goal: one visual language across both, legible to municipal staff and citizens.

## 1. Principles
- Data-first: forecasts, stress, and plans must be readable in <5s.
- Geographic thinking: every ward-level number links to the map where possible.
- Trust: provisional values (synthetic data, uncalibrated thresholds) are always labeled as such.

## 2. Colors
| Token | Value | Use |
|---|---|---|
| `--ws-deep` | `#0B3D62` | Header, nav, primary text on light |
| `--ws-primary` | `#147CB5` | Primary buttons, links, active states |
| `--ws-accent` | `#22B8CF` | Highlights, forecast lines, info |
| `--ws-bg` | `#F4F7FA` | App background |
| `--ws-surface` | `#FFFFFF` | Cards, panels |
| `--ws-border` | `#DCE4EC` | Dividers, card borders |
| `--ws-text` / `--ws-muted` | `#1A2B3C` / `#5B7288` | Text / secondary text |
| Stress Safe | `#2E9E5B` bg `#E3F4E9` | WAR band (threshold TBD, see PRD) |
| Stress Moderate | `#C9A100` bg `#FFF4CC` | — |
| Stress High | `#E07B00` bg `#FFE8CC` | — |
| Stress Shortage | `#D64545` bg `#FDE3E3` | — |

Stress colors must match GIS choropleth + dashboard badges + app banners exactly. Never use red/green alone to convey stress — always pair with label text + icon.

## 3. Typography
- Dashboard (React): Inter (fallback system-ui). H1 24/32, H2 20/28, H3 16/24, Body 14/20, Caption 12/16.
- Citizen app (Flutter): Roboto (Android) / SF (iOS) via platform default; same size ramp.
- Numbers: tabular-nums for all ML values, ML units always shown (`ML`, `WAR 0.90`, `MAPE 8.2%`).

## 4. Spacing / Layout
- 8px base grid. Card radius 12px, padding 16–24px. Page max-width 1280px dashboard.
- Dashboard layout: left nav (Forecasts, Reservoirs, Stress, Supply Plan, GIS, Leakage, Complaints) + top ward/date selector + main cards.
- Mobile: bottom nav (Schedule, Alerts, Complaints, Account); banner slot for shortage alerts.

## 5. Components
- **Ward selector + date-range picker:** global, persists across pages; drives all API calls.
- **Forecast chart:** line chart (actual vs. predicted) per horizon tabs [1-day|3-day|7-day]; tooltip shows value + model version. Recharts/Plotly on web; `fl_chart` on Flutter.
- **Stress badge:** colored pill + label + WAR value. Click → explains gap calculation.
- **Supply plan table:** ward rows, allocated ML, gap, alert icon for High/Shortage.
- **Map (Leaflet web):** OSM tiles, ward polygons colored by stress, reservoir markers with popup (storage %, available ML).
- **Complaints:** status stepper (Filed → In-progress → Resolved).
- **Empty/loading/error:** skeleton for charts; explicit "no data for ward+date" state; error card with retry, never blank.

## 6. Charts / Data-viz Rules
- Always show horizon, model name/version, and data provenance (real vs. synthetic) near forecasts.
- Y-axis starts at 0 for ML; WAR axis fixed 0–1.2 with threshold bands drawn.
- No 3D, no truncated axes.

## 7. Accessibility / i18n
- Contrast ≥4.5:1 for text. All form inputs labeled. Keyboard-navigable dashboard. Touch targets ≥44px in app.
- Citizen app strings externalized for future regional-language support; dates/numbers locale-formatted.

## 8. CSS Framework Decision (open)
Tailwind vs. MUI not yet chosen (see IMPLEMENTATION_PLAN §8 Phase 9). Either must implement the tokens above. Record the choice in `Context.md` when made.
