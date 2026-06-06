# Slice 26 — Exchange

> Shared channel for **Claude, Codex, ChatGPT, User**.
> **Every entry begins with `[Author — YYYY-MM-DD]`** so it's always clear who is speaking.
> Append-only. Communication, NOT commands: a finding becomes Codex work only via a
> User-approved task spec. Each author writes under their own heading; "Open questions"
> and "User — decisions" are shared.
> Commit access: only Codex (its own branch) and the User. ChatGPT and Claude hand their text
> to the User, who commits it.

## Codex — handoff & notes
- [Codex — YYYY-MM-DD] <what was built, tests run + results, deviations>
<!-- Include an acceptance-to-test mapping in your handoff:
| Acceptance criterion | Test | Covered? |
| --- | --- | --- |
-->
- [Codex — 2026-06-06] Built slice 26 spec revision history. Added one migration, `0004_add_spec_revisions`, which replaces the obsolete placeholder `spec_revisions` shape with the slice-26 audit table (`revision_number`, text/status/source/change_type snapshot, `created_at` default, `UNIQUE(spec_id, revision_number)`, STRICT, spec index). Added `record_spec_revision` and wired it into Spec create, text edit, and status decision commits; created specs flush before revision recording so revision #1 is in the same transaction. Added idempotent seed-run backfill for specs with zero revisions; for pre-existing specs this uses the current spec state as the accepted baseline because original creation state is not recoverable. Added `GET /api/specs/{id}/revisions` and a read-only `SpecHistoryPanel` opened from each spec node.

| Acceptance criterion | Test | Covered? |
| --- | --- | --- |
| Every spec accrues immutable created/text_edited/status_changed snapshots | `backend/tests/test_spec_revisions.py::test_create_spec_records_created_revision`; `test_text_edit_records_revision_and_preserves_original`; `test_decide_spec_records_status_revision`; `test_child_spec_creation_records_created_revision` | Yes |
| Existing specs are backfilled with baseline created revision idempotently via seed | `backend/tests/test_seed.py::test_seed_backfills_missing_spec_revisions_idempotently` | Yes |
| History is viewable per spec in chronological order through API and UI | `backend/tests/test_specs_api.py::test_specs_api_lists_revisions_ascending_and_missing_404`; `frontend/src/components/SpecHistoryPanel.test.tsx` | Yes |
| Manual spec history is distinguishable from AI-created then accepted history | `backend/tests/test_spec_revisions.py::test_manual_and_ai_accepted_histories_are_distinct` | Yes |
| Migration is a clean single-table create with unique constraint and spec index | `backend/tests/test_migration_0004.py::test_migration_0004_creates_spec_revisions_table_and_unique_constraint` | Yes |
| Every touched frontend file is under 200 lines | `wc -l frontend/src/components/SpecHistoryPanel.tsx frontend/src/components/SpecHistoryPanel.test.tsx frontend/src/components/SpecNode.tsx frontend/src/components/SpecNode.test.tsx frontend/src/api/specs.ts frontend/src/types/spec.ts` | Yes |

Tests run:
- Backend: `.venv/bin/pytest` from `backend/` -> 271 passed.
- Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` -> 22 files / 53 tests passed.
- Frontend typecheck: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm typecheck` -> passed.
- Frontend build: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm build` -> passed.

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale
