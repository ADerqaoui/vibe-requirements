# Slice 28 — Operational hardening (startup DB setup + global error visibility)

Branch: `slice-28` (from `main`). Scope: make the backend self-healing and faults visible, killing the bug class that caused the generation-500 and accept-500 incidents (live DB drifting behind the code, surfaced as opaque 500s). Three parts: (A) apply migrations + seed at app startup regardless of launch method; (B) a global exception handler that logs tracebacks and returns structured errors; (C) remove the dangerous migration fallback in `run-backend.sh`. **Backend-only.** Addresses review findings H1, H2, M4 (and lays the foundation for M1).

## In scope

### A. Startup DB setup (migrate + seed), gated and loud
1. **Settings flag:** add `auto_migrate_on_startup: bool = True` to `app/config.py::Settings` (env-overridable, e.g. `AUTO_MIGRATE_ON_STARTUP=false`). Default true.
2. **Bootstrap function:** new `app/bootstrap.py` with `run_startup_db_setup(settings)` that, when the flag is true:
   - builds an Alembic `Config` with `script_location` resolved **absolutely** (e.g. from the package path, not cwd — so it works no matter where uvicorn is launched) and `sqlalchemy.url = settings.database_url`, then runs `command.upgrade(config, "head")`;
   - then runs the existing seed (`app.seed.run.main()`), which is idempotent;
   - on **any** failure, logs the error loudly (`logging.exception(...)`) and **re-raises** so the app refuses to start with a clear message — never swallow, never stamp.
3. **Lifespan wiring:** convert `create_app()` to pass a FastAPI `lifespan` (asynccontextmanager) that calls `run_startup_db_setup(settings)` on startup, so migrate+seed run on **every** launch method (uvicorn directly, Docker, IDE) — not just `run-backend.sh`. This is the core fix: the app can no longer serve against a DB that's behind the code.
4. The flag exists so the **test suite** disables startup migration (tests manage their own DBs) — set `AUTO_MIGRATE_ON_STARTUP=false` (or settings override) in the app/test fixtures.

### B. Global exception handler + logging (H2)
5. Add an unhandled-exception handler (in `app/api/errors.py`, registered in `create_app` via `app.add_exception_handler(Exception, ...)`): it logs the full traceback (`logging.exception`) and returns `JSONResponse(500, {"error": "internal_error", "detail": str(exc)})`. (Including `detail` is acceptable for this single-user LAN tool and aids diagnosis; note in the handoff it would be generic for multi-user.)
6. Keep all existing domain-error mappings and `cost_ceiling_response` unchanged — this is the catch-all **net** beneath them, so an unexpected fault (like the missing-table commit error) becomes a logged traceback + a structured 500 instead of an opaque one. Do **not** rework per-route error handling in this slice (that standardization is a follow-up); just add the net.

### C. `run-backend.sh` cleanup (H1)
7. Remove the dangerous line `alembic upgrade head 2>/dev/null || alembic stamp head` — the `2>/dev/null` hides migration errors and `|| alembic stamp head` marks the DB as current without applying anything, masking a broken schema. Since startup (A) now handles migrate+seed, simplify the script to: `cd backend`, activate the venv, and `exec uvicorn ...`. (No migrate/seed/stamp in the script.) Add a one-line comment noting the app applies migrations + seed on startup.

## Tests (deterministic)
- **schema-drift guard:** apply `alembic upgrade head` to a fresh temp DB, then assert **every** table in `Base.metadata.tables` exists in the DB. This catches a model added without a migration (the drift class that unit tests otherwise miss).
- **bootstrap success:** with the flag on, `run_startup_db_setup` invokes upgrade-to-head then seed (assert via a temp DB that tables exist and seeded reference rows are present; or mock `command.upgrade` + seed and assert both called in order).
- **bootstrap failure is loud:** if `command.upgrade` raises, `run_startup_db_setup` re-raises (does not swallow, does not call stamp) — assert the exception propagates.
- **flag off:** with `auto_migrate_on_startup=false`, `run_startup_db_setup` does nothing (no upgrade/seed call).
- **global handler:** a route that raises an unexpected exception returns HTTP 500 with body `{"error": "internal_error", ...}` and the traceback is logged (use `TestClient(raise_server_exceptions=False)`).
- existing suite stays green with the fixtures setting the flag off.

## Out of scope (build NO behavior)
- Standardizing per-route error mapping (M1) — follow-up; this slice only adds the global net.
- The blacklist fix (slice 29), dead-schema cleanup (slice 30), complexity refactor (slice 31), tooling gate (slice 32).
- Multi-instance migration locking (single-user; note as a deferred concern).
- Changing what any feature does or any schema.

## API / behavior shapes
- New `app/bootstrap.py::run_startup_db_setup(settings)`.
- `create_app()` gains a `lifespan` running it; `Settings.auto_migrate_on_startup` added.
- New global `Exception` handler → 500 `{error: "internal_error", detail}`.
- `run-backend.sh` simplified (no stamp/`2>/dev/null`).
- No schema changes, no new endpoints.

## Suggested file layout (one entity per file)
`app/bootstrap.py` (startup setup); edit `app/config.py` (flag), `app/main.py` (lifespan + handler registration), `app/api/errors.py` (handler), `scripts/run-backend.sh`. Tests: `backend/tests/test_bootstrap.py`, `backend/tests/test_schema_drift.py`, extend an api test for the global handler; adjust the app/test fixtures to set the flag off.

## Acceptance criteria
- Launching the backend by **any** method (bare `uvicorn`, Docker, IDE, or the script) applies migrations + seed before serving, or refuses to start with a loud, specific error if a migration fails — the stale-DB 500 class is gone.
- An unexpected exception anywhere returns a structured 500 with a server-side logged traceback, not an opaque 500.
- `run-backend.sh` no longer hides or stamps over migration failures.
- Backend `pytest` green incl. the new drift/bootstrap/handler tests; frontend untouched (run its checks once to confirm no incidental breakage).
- Handoff in `docs/exchange/slice-28.md` with acceptance-to-test mapping.

## Constraints
- Backend-only. Startup setup is gated by `auto_migrate_on_startup` so tests control it; on failure it RE-RAISES (no swallow, no stamp). Resolve the alembic `script_location` absolutely so startup works regardless of cwd. The global handler is additive — leave existing domain mappings intact. One branch, one PR, no self-merge. Checks green per docs/MERGE-CHECKLIST.md.