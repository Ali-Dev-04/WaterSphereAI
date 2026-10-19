# Testing.md — WaterSphere AI

Expands IMPLEMENTATION_PLAN §10. No phase gate passes with red tests.

## 1. Levels + Commands
| Level | Scope | Command (proposed) |
|---|---|---|
| Unit (Py) | lag/rolling features, WAR/stress/supply logic, services | `pytest backend/ ml/ -q` |
| Unit (FE) | React components, Flutter widgets | `npm test` / `flutter test` |
| Integration | FastAPI↔Postgres, backend↔inference, clients↔API | `pytest tests/integration -q` + Postman collection |
| API contract | status codes, Pydantic schema, auth matrix, errors | `pytest tests/api -q` (OpenAPI snapshot) |
| ML validation | schema/range checks, beats baseline, val↔test gap, leakage checks, determinism | `pytest ml/tests -q` + comparison-table review |
| E2E | admin journey + citizen journey (Phase 13 criteria) | staging script/manual run |
| Performance | p95 API latency, inference ms/req | `locust` or k6 smoke (thresholds TBD) |
| Security | bypass, RBAC boundary, injection, secret scan | checklist in Security.md §6 |

## 2. ML-Specific Gates (must all pass)
- [ ] Train/val/test chronological (70/15/15 starter, adjust to size); no shuffle.
- [ ] Tuning on validation only; test touched once per selection cycle.
- [ ] All 4 models (or MVP subset) beat seasonal-naive on 1-day val MAE/RMSE.
- [ ] No future leakage: rolling/lag use `shift(1)` minimum; verified by unit test.
- [ ] Edge cases covered: sparse-history ward, missing reservoir reading.
- [ ] Comparison table (Model × MAE/RMSE/MAPE/R² × horizon) fully populated.

## 3. API / E2E Assertions
- Worked example: forecast 500 ML + available 450 ML → gap 50, WAR 0.90, category per current thresholds.
- Supply plan never allocates > available (minus reserve %).
- Full journeys: `admin login → forecast → stress → plan → citizen alert → complaint filed → admin sees it` with zero manual DB edits.
- Auth matrix: every endpoint × {no token, citizen-other-ward, admin} returns expected 401/403/200.

## 4. Coverage / Quality Bars
- Backend services (WAR, allocator, inference): ≥80% line coverage. Feature-eng functions: 100% on leakage-sensitive paths.
- `ruff`, `black --check`, `mypy` (py), `eslint`, `dart analyze` clean before merge.

## 5. Data Test Fixtures
Keep `tests/fixtures/` with: 30-day 2-ward synthetic consumption set (known rolling values), reservoir readings, and expected WAR/stress outputs. Label synthetic provenance explicitly.
