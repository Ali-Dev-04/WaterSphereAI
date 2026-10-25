# Agents.md — Working Agreement for AI / Human Agents

This file governs how any agent (AI model, developer, contributor) works in this repo. Read it before writing code or docs.

## 1. Source of Truth (read order)
1. `Context.md` — current stage, latest decisions, what changed. Read first, update last.
2. `PRD.md` — what to build and why.
3. `Architecture.md` — how the system fits together.
4. `Docs/IMPLEMENTATION_PLAN.md` — phase roadmap (§7–9), dependencies, acceptance criteria.
5. `Security.md`, `Testing.md`, `Code_style.md`, `Design_System.md` — constraints for their areas.
6. `Docs/WaterSphere AI_Project_Complete_Development_Context.pdf` + `Docs/Architecture.jpeg` — original research context.

If these conflict, `Context.md` + explicit user instruction win. Flag the conflict in `Context.md`.

## 2. Project State (verified 2026-10-25)
**Implemented and running locally through Phase 14.** Do not assume otherwise, but still verify before claiming specifics.

- `backend/` — FastAPI, 22 API operations, 11-table PostgreSQL schema, Alembic head `c8f2a6b1e4d9`, JWT + ward-scoped RBAC, guest complaints with photo upload.
- `frontend/` — React 18 + Vite (plain JSX), public landing page, sign-in/registration/guest-report card, role-aware tabs, plain-CSS light municipal theme.
- `scripts/` — data generation/validation, preprocessing, features, train, evaluate, `e2e_check.py`, drift + backup.
- `models/` — 12 trained artifacts + `manifest.json`/`active.json`; `data/` — bmc-v1 dataset and reports.
- `mobile/` — **does not exist** (Flutter app is Phase 11, deferred).
- Verification baseline: `pytest backend/tests` **28/28**, `scripts/e2e_check.py` **38/38**, `npm run build` PASS, CI green (backend + ml-smoke + frontend).

Remaining work: staging deploy (Phase 15), Flutter app, authoritative ward GIS, mobile-width UI sweep, and the open WAR availability-basis decision.

## 3. How to Work
- **Verify before synthesizing.** Inspect files yourself. Never present guesses as facts. If you checked, say what you checked.
- **Smallest sufficient change.** Prefer editing existing files over creating new ones. No new top-level docs without being asked.
- **Use dedicated tools:** `read`/`edit`/`write` for files; `shell` only for real commands (tests, builds). Quote paths with spaces (`WaterSphere AI`).
- **Parallelize independent reads** (multiple `read`/`glob` in one turn). Sequence dependent writes.
- **Confirm with execution** where reasonable: run tests, reproduce calculations (e.g. WAR = 0.90 worked example), sanity-check feature code on synthetic inputs.

## 4. Scope Discipline
- Respect MVP / Advanced / Future boundaries in `PRD.md §6`. Do not build Advanced items (LP/MILP, full GIS, FCM) when asked for MVP.
- Rainfall/weather is out of scope — do not add it unless the user explicitly rescopes.
- Leakage supervised models require labels; default to unsupervised (IsolationForest) until labels are confirmed.

## 5. Mandatory: Keep Context.md Updated
`Context.md` is the living log. **Every task that changes code, schema, models, thresholds, decisions, or stage must append to it in the same turn.**

Update format (append row, bump `Last Updated` + `Stage` if it changed):
```md
| YYYY-MM-DD | task/scope | What changed + files touched | stage before → after | open items |
```

Rules:
- Never rewrite history — append only.
- Record: decision + reason, assumption vs. confirmed fact, deviations from `IMPLEMENTATION_PLAN.md`.
- If you completed a phase gate (e.g. Phase 1 dataset ready), update `Current Stage`, `Phase Gates`, and `Next Steps` sections.
- If the user corrects you, record it under `Corrections / Constraints` so future turns obey it.

A task is not done until `Context.md` is updated.

## 6. Conventions
- Code style: `Code_style.md`. Security: `Security.md` (JWT/RBAC from day one, no secrets in git). Tests: `Testing.md`. UI: `Design_System.md`.
- DB/API changes require: migration (Alembic), OpenAPI still valid, traceability row (which FR).
- ML changes require: seed fixed, train/val/test split chronological (no shuffle), validation-only tuning, test set touched once, comparison-table row updated.
- Never hardcode WAR thresholds, model paths, or secrets — config or DB table + env vars.

## 7. Definition of Done (per task)
- [ ] Requested change implemented, minimal and verified (test run or calculation check).
- [ ] No scope creep into Advanced/Future.
- [ ] Relevant checklist in `Testing.md` / `Security.md` considered.
- [ ] `Context.md` appended.
