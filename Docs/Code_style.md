# Code_style.md — WaterSphere AI

## 1. General
- Keep diffs small; one concern per PR/task. No commented-out code, no dead files. Every module has a single responsibility matching Architecture.md layers (routers → services → repository; preprocessing → features → training → inference).
- Names: descriptive, no abbreviations beyond `ML`, `WAR`, `FCM`. Ward/date keys always `ward_id`, `date` (ISO `YYYY-MM-DD`).

## 2. Python (backend + ML)
- 3.x, type hints on all public functions. Formatter `black` (line length 100) + linter `ruff`. Imports sorted (stdlib → third-party → local).
- FastAPI: Pydantic v2 schemas per route; router = thin, logic in `services/`; DB in `repositories/`. Config via `pydantic-settings`, never hardcoded thresholds/paths/secrets.
- ML: fixed seeds (`random`, `numpy`, `tensorflow`/`torch`); chronological splits only (no shuffle); lag/rolling computed **per ward** (`.groupby('ward_id').shift()`); unit-test feature fns on synthetic inputs; log `model_version` + `data_version` with every artifact.
- Example:
```python
def rolling_demand(df: pd.DataFrame, window: int = 7) -> pd.Series:
    return df.sort_values("date").groupby("ward_id")["demand"].transform(
        lambda s: s.shift(1).rolling(window, min_periods=window).mean()
    )
```

## 3. JavaScript/React (dashboard)
- **Plain JSX, not TypeScript** (`frontend/src/**/*.jsx`); no type-checking step and no ESLint/Prettier config in CI today — `npm run build` is the enforced gate.
- Functional components + hooks. Data fetching lives in the component's `useEffect`/helper or `api.js` (axios instance with `VITE_API_URL`), not in JSX markup.
- One component per file (`Forecasts.jsx`, `Complaints.jsx`); props kept explicit and small; charts receive ward/date/horizon and show model version + provenance.
- **Styling:** plain CSS with design tokens in `frontend/src/styles.css` (no Tailwind/MUI). Light municipal theme only — no glows, decorative gradients, backdrop-blur, or neon (see `Design_System.md`).
- Naming: PascalCase components/files, `camelCase` functions, `ward_id`/`date` unchanged in API payloads.
- Configuration: never hardcode user-visible numbers (ward count, date bounds, WAR bands, model version) — read `GET /api/meta`.

## 4. Dart/Flutter (citizen app)
- `dart format` + `flutter analyze` clean. Feature folders (`features/schedule/`, `features/complaints/`); HTTP via `dio`/`http` against same typed endpoints; strings in localization files.

## 5. SQL / Alembic
- Lowercase snake_case tables/columns matching Architecture.md §4 (11 tables, current head `c8f2a6b1e4d9`). Every migration reversible (`upgrade` + `downgrade`), one semantic change each. Add `JSONB meta` only where plan allows extensibility. New columns that must accept legacy rows are added nullable (as done for guest complaints).

## 6. Git
- Branches `feat/<phase>-<short>` / `fix/...`. Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`). Never commit `.env`, `*.db`, model binaries (>10MB → object storage + pointer), or Firebase JSON.
