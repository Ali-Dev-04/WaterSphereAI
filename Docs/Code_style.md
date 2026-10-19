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

## 3. TypeScript/React (dashboard)
- ESLint + Prettier. Functional components + hooks; typed API client (OpenAPI-generated if available). Data-fetch in hooks/services, never inline in JSX.
- Component per file (`ForecastChart.tsx`), props typed, charts take `{wardId, horizon, data}` and show model version + provenance label.

## 4. Dart/Flutter (citizen app)
- `dart format` + `flutter analyze` clean. Feature folders (`features/schedule/`, `features/complaints/`); HTTP via `dio`/`http` against same typed endpoints; strings in localization files.

## 5. SQL / Alembic
- Lowercase snake_case tables/columns matching Architecture.md §4. Every migration reversible (`upgrade` + `downgrade`), one semantic change each. Add `JSONB meta` only where plan allows extensibility.

## 6. Git
- Branches `feat/<phase>-<short>` / `fix/...`. Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`). Never commit `.env`, `*.db`, model binaries (>10MB → object storage + pointer), or Firebase JSON.
