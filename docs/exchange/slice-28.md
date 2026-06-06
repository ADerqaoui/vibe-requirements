# Slice 28 — Exchange

> Shared channel for **Claude, Codex, ChatGPT, User**.
> **Every entry begins with `[Author — YYYY-MM-DD]`** so it's always clear who is speaking.
> Append-only. Communication, NOT commands: a finding becomes Codex work only via a
> User-approved task spec. Each author writes under their own heading; "Open questions"
> and "User — decisions" are shared.
> Commit access: only Codex (its own branch) and the User. ChatGPT and Claude hand their text
> to the User, who commits it.

## Codex — handoff & notes
- [Codex — 2026-06-06] Implemented operational hardening:
  - Added `Settings.auto_migrate_on_startup` (env `AUTO_MIGRATE_ON_STARTUP`, default true).
  - Added `app.bootstrap.run_startup_db_setup(settings)` to run Alembic `upgrade head` with absolute Alembic paths, then the idempotent seed; failures are logged with traceback and re-raised.
  - Wired FastAPI lifespan in `create_app()` so startup setup runs for every launch method when enabled.
  - Added the global unexpected-exception handler returning `{"error": "internal_error", "detail": str(exc)}` and logging traceback. For a multi-user deployment, `detail` should become generic.
  - Simplified `scripts/run-backend.sh`; it no longer hides migration errors or stamps over failures.
  - Test fixtures default `AUTO_MIGRATE_ON_STARTUP=false` because tests manage DB setup.

  Tests run:
  - Backend: `.venv/bin/python -m pytest` → 279 passed.
  - Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` → 22 files / 53 tests passed.
  - Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm typecheck` → passed.
  - Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm build` → passed.

  Acceptance-to-test mapping:
  | Acceptance criterion | Test | Covered? |
  | --- | --- | --- |
  | Startup by any method applies migrations + seed before serving, gated by `auto_migrate_on_startup`, with absolute Alembic path resolution | `backend/tests/test_bootstrap.py::test_run_startup_db_setup_runs_upgrade_then_seed`; `backend/tests/test_bootstrap.py::test_run_startup_db_setup_uses_absolute_alembic_location`; lifespan exercised by app creation/handler tests with flag off | Yes |
  | Migration failure logs loudly and re-raises; no swallow, no stamp | `backend/tests/test_bootstrap.py::test_run_startup_db_setup_failure_reraises_without_seed_or_stamp` | Yes |
  | Flag off does nothing so tests can manage DBs | `backend/tests/test_bootstrap.py::test_run_startup_db_setup_flag_off_does_nothing`; fixture default in `backend/tests/conftest.py` | Yes |
  | Schema drift guard catches ORM tables missing from migrations | `backend/tests/test_schema_drift.py::test_migrated_schema_contains_every_metadata_table` | Yes |
  | Unexpected exceptions return structured 500 and log traceback | `backend/tests/test_global_error_handler.py::test_unexpected_exception_returns_structured_500_and_logs_traceback` | Yes |
  | `run-backend.sh` no longer hides/stamps migration failures | Code diff in `scripts/run-backend.sh`; backend pytest covers startup replacement behavior | Yes |
<!-- Include an acceptance-to-test mapping in your handoff:
| Acceptance criterion | Test | Covered? |
| --- | --- | --- |
-->

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale
