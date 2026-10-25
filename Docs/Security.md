# Security.md — WaterSphere AI

## 1. Principles
Build auth in during Phase 6, audit in Phase 14. Municipal + citizen data; no bolt-on security. Deny by default; least privilege (ward-scoped staff where applicable).

## 2. Authentication (implemented)
- **JWT bearer, 60-minute expiry**, HS256. Passwords hashed with bcrypt (direct `bcrypt`, not `passlib`). No plaintext secrets stored or logged. **Refresh-token rotation is not implemented** — a token simply expires and the user signs in again (acceptable for pilot; add refresh before public launch).
- **Citizen registration is open self-registration**, forced to the `citizen` role with the ward locked at sign-up; admins are provisioned only (no self-registration to admin — asserted in e2e, `403`). OTP/phone verification is not implemented (open decision in `Context.md`).
- **Guest reporting is the only anonymous write path**: `POST /api/complaints/public`, rate-limited 5/min/IP, no account and no token issued.
- Secrets (DB URL, `JWT_SECRET`, CORS origins, WAR bands, reserve %) come from env vars / `.env` only; `.env` is gitignored and `.env.example` ships dummy values. Dev seeded passwords (`admin123` / `citizen123`) are documented only in `README.md`/`demo.md` and must be rotated before any shared deployment.

## 3. Authorization (RBAC — implemented)
Roles: `admin`, `citizen`. Enforced server-side via FastAPI dependencies on every protected route; the UI merely hides things. Ward scoping is applied by filtering on the token's `ward_id`, and out-of-ward requests return **403**, not empty data.

| Endpoint | Admin | Citizen |
|---|---|---|
| population/consumption/reservoir (read) | all wards | own ward only |
| forecast/water-stress/supply-plan/gis (read) | all wards | own ward only |
| `GET /api/leakage-risk`, `/api/maintenance` | all | none (403) |
| `GET /api/complaints` | all (any ward, both reporters) | own submissions only |
| `POST /api/complaints` | any ward | own ward only (forced) |
| `PATCH /api/complaints/{cid}` | allowed | 403 |
| `GET /api/complaints/{cid}/photo` | **admin only** | 403 |
| public: `/api/health`, `/api/meta`, `/api/public/wards`, `POST /api/complaints/public` | no token | no token |

401 = unauthenticated/malformed/expired token; 403 = authenticated but not permitted (role or ward). Error bodies do not echo other wards' data. Covered live by the e2e auth matrix (401/403/404/409).

## 4. Input Validation / Abuse (implemented)
- Pydantic v2 schemas on every route (ward IDs, dates, ranges, enums). SQLAlchemy parameterized queries only — no raw SQL string building.
- **Rate limits (slowapi)**: login 10/min/IP, guest complaint submission 5/min/IP. **Residual:** counters are in-process/in-memory, so they reset on restart and are per-worker — move to Redis before public deployment.
- **Guest photo upload**: mandatory; JPEG/PNG/WEBP only; **5 MB cap**; MIME is decided by **magic-byte sniffing** (client `Content-Type` and filename are not trusted); stored under a server-generated UUID filename; path traversal blocked on read; download is admin-only and served as an authorized blob.
- Complaint text is length-bounded; `others` requires a ≥25-character description on the guest form (server enforces its 10-char floor for all types). Ward IDs are validated against the DB, unknown wards return 404.
- FCM (Phase 11, not built): server must send to ward-topic tokens only; never trust client-supplied ward for alert targeting.

## 5. Transport / Storage / Deploy
- CORS uses an explicit origin allowlist (`CORS_ORIGINS`, default `http://localhost:5173`); no `*` with credentials. HTTPS/HSTS is a staging-deploy task (Phase 15) — local dev is HTTP.
- Postgres: Alembic-only migrations (current head `c8f2a6b1e4d9`, 11 tables). The app connects with a single DB user; a least-privilege split user is a deploy task. Local volume is the only copy until managed snapshots are enabled (`scripts/backup_db.sh` provides `pg_dump` snapshots).
- Logs are structured application logs; no passwords or tokens are logged. PII exposure is limited to complaint reporter name/address/description, visible to admins only. Sentry/APM remains an open decision.
- Uploaded complaint photos live on the API filesystem under `uploads/` (not object storage) — fine for pilot, needs object storage + lifecycle policy at scale.

## 6. Pre-Deploy Checklist (Phase 14 gate)
- [x] Auth + RBAC boundary tests automated: pytest suite + live e2e auth matrix (no-token 401, tampered token 401, citizen-other-ward 403, admin-only routes 403, duplicate username 409, unknown ward 404).
- [x] No `.env`, keys, or Firebase JSON committed; `.gitignore` covers them.
- [ ] Dependency vulnerability scan run (`pip-audit` / `npm audit`) — not yet in CI.
- [x] JWT expiry (≈60 min, asserted in e2e) and bcrypt password hashing verified.
- [x] Upload validation verified (magic bytes, 5 MB cap, admin-only read).
- [ ] Rate limits verified on staging with a shared store (currently in-memory).
- [ ] Fresh production `JWT_SECRET`, rotated dev passwords, managed DB backups + tested restore.
- [ ] HTTPS/HSTS + production CORS origins.

Results are recorded in `Context.md`.
