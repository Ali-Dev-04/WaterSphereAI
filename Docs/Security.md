# Security.md — WaterSphere AI

## 1. Principles
Build auth in during Phase 6, audit in Phase 14. Municipal + citizen data; no bolt-on security. Deny by default; least privilege (ward-scoped staff where applicable).

## 2. Authentication
- JWT bearer (short expiry, e.g. 30–60 min) + refresh-token rotation. Hash passwords with bcrypt (`passlib`). Never store or log plaintext secrets.
- Citizen registration model TBD (self-reg vs. provisioned, OTP?) — record decision in `Context.md`; implement accordingly with rate-limited OTP if chosen.
- Secrets (DB URL, JWT secret, Firebase creds, CORS origins) via env vars / Render+Netlify settings only. `.env` local, never committed. Provide `.env.example` with dummy values.

## 3. Authorization (RBAC)
Roles minimum: `admin`, `citizen` (add `ward_staff` / `super_admin` only if decided). Enforce server-side on every route via dependencies, never client-side only.
| Endpoint | Admin | Citizen |
|---|---|---|
| population/consumption/reservoir (read) | all wards | own ward only |
| forecast/water-stress/supply-plan (read) | all | own ward only |
| complaints | all (update status) | create own, read own |
| leakage-risk | all | none (or own-ward summary if decided) |

Return 401 (unauthenticated) vs. 403 (unauthorized) correctly; no data leakage in error messages.

## 4. Input Validation / Abuse
- Pydantic schemas on all inputs (ward IDs, dates, ranges); reject unknown fields where appropriate. Parameterized ORM queries only — no raw SQL string building.
- Rate-limit public/auth endpoints (`slowapi` or platform limits). Upload/CSV import (if added) needs size caps + schema validation.
- FCM: server sends to ward-topic tokens only; never trust client-supplied ward for alert targeting.

## 5. Transport / Storage / Deploy
- HTTPS everywhere (Render/Netlify default); HSTS on dashboard. CORS allowlist exact origins, no `*` with credentials.
- Postgres: managed backups, least-privilege DB user for app, migrations via Alembic only.
- Logs: structured, no PII/passwords/tokens. MVP: Render logs; production path: Sentry or equivalent (open decision).

## 6. Pre-Deploy Checklist (Phase 14 gate)
- [ ] All routes have auth + RBAC tests (bypass + boundary).
- [ ] `git secrets` scan clean; no `.env`, keys, or Firebase JSON in history.
- [ ] Dependency vulnerability scan run.
- [ ] JWT expiry/refresh verified; password hashing verified.
- [ ] Rate limits + CORS verified on staging.
Results recorded in `Context.md`.
