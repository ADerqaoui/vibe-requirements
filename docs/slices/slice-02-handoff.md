# Slice 02 — Handoff

**Branch:** slice-02
**Spec:** docs/slices/slice-02.md

## What was built
- Added the full Alembic schema migration from `architecture.md` section 2, including all base tables as `STRICT`, indexes, cascades, `blacklist_entries` parent check, and `blacklist_vec` virtual table.
- Added one SQLAlchemy ORM model per base table under `backend/app/models/`.
- Added idempotent reference seeding for 3 disciplines, 12 layers, and the specified V-model layer parent rules via `python -m app.seed.run`.
- Added Projects CRUD service, schemas, and `/api/projects` routes for list/create/get/rename/delete, including duplicate-name 409 handling and DB cascade delete.
- Replaced the slice-1 frontend health card with a minimal Projects column supporting list, create, select/highlight, rename, and delete.
- Added backend tests for migration/seed and Projects API behavior, plus a frontend smoke test for rendering a mocked project list.
- Documented the seed command in `README.md`.

## Tests run
- [x] `cd backend && .venv/bin/pytest` — 4 passed.
- [x] `cd backend && .venv/bin/alembic upgrade head` — migration applied cleanly after removing a partial local DB created during earlier failed verification.
- [x] `cd backend && .venv/bin/python -m app.seed.run` twice — both runs completed without error.
- [x] Backend runtime check: `GET /api/health` returned `{"status":"ok","database":"ok","ollama":"ok"}`.
- [x] Backend runtime check: `GET /api/projects` returned `[]`.
- [x] `cd frontend && pnpm test` — 1 test passed.
- [x] `cd frontend && pnpm build` — production build passed.
- [x] Frontend runtime check: Vite served `/` with HTTP 200 and proxied `/api/projects` to the backend with response `[]`.

## Deviations from spec
- None.

## Open questions / risks
- FastAPI's sync TestClient path hangs in this environment with the installed Starlette/httpx combination, so API tests use `httpx.AsyncClient` + `ASGITransport`.
- The Projects detail endpoint returns `needs: []` for now as specified by this slice; Needs loading remains out of scope.
