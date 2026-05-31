# Slice 10 — Exchange

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
- [Codex — 2026-05-31] Implemented slice 10 Inspector, lifecycle decisions, and NeedList split.

  Built:
  - Added Alembic migration `0002_add_spec_inspections` with a STRICT `spec_inspections` table, `spec_id` `ON DELETE CASCADE`, and `idx_spec_inspections_spec`.
  - Added single-model inspector prompt/parser/service/API. The parser is permissive, case-insensitive, defaults missing criteria to `UNCLEAR`, skips structural headers, and returns 422 when zero criteria parse.
  - Inspector service uses the existing gateway logging path and only persists `spec_inspections` after a successful gateway call and successful parse. Gateway failure and parser-empty paths write no inspection row.
  - Added `POST /api/specs/{spec_id}/decision` for only `accepted` and `rejected`; `pending` remains rejected by validation.
  - Added `GET /api/specs/{spec_id}/inspections` newest-first and `POST /api/specs/{spec_id}/inspect`.
  - Extended `SpecOut` and spec-tree nodes with `latest_inspection_id` computed from existing inspection rows, without schema changes to `specs`.
  - Frontend adds inspection model picker, Inspect button, inline findings panel, Accept/Reject decisions, and status badges in the existing recursive `SpecList`.
  - Split `NeedRow.tsx` and `NeedCreateForm.tsx`; `NeedList.tsx` is now 191 lines.

  Verification:
  - `.venv/bin/pytest` from `backend/`: 102 passed, 74 warnings.
  - `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` from `frontend/`: 8 files passed, 19 tests passed.
  - `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm exec tsc --noEmit` from `frontend/`: passed.

  Acceptance-to-test mapping:

  | Acceptance criterion | Test | Covered? |
  | --- | --- | --- |
  | Clicking Inspect with an enabled model runs inspection, persists a row, and renders PASS/FAIL findings. | `test_inspection_api_persists_and_lists_newest_first`, `test_inspector_service_persists_parsed_findings`, `SpecList.test.tsx` inspection test | Yes |
  | Accept transitions to `accepted`; Reject transitions to `rejected`; status is visible in the tree. | `test_decision_api_accepts_and_rejects`, `SpecList.test.tsx` decision badge test | Yes |
  | `POST /api/specs/{id}/inspect` returns 200, 404, 409, 422 parser-empty, and 502 gateway failure with no inspection row on failures. | `test_inspection_api_persists_and_lists_newest_first`, `test_inspection_api_missing_spec_and_model_conflicts`, `test_inspection_api_parser_empty_and_gateway_failure_write_no_rows` | Yes |
  | `POST /api/specs/{id}/decision` returns 200 for valid decisions, 422 invalid value, and 404 missing Spec. | `test_decision_api_accepts_and_rejects`, `test_decision_api_is_idempotent_for_same_status`, `test_decision_api_rejects_invalid_and_missing_spec` | Yes |
  | `GET /api/specs/{id}/inspections` returns newest-first list scoped to the Spec. | `test_inspection_api_persists_and_lists_newest_first` | Yes |
  | Migration 0002 round-trips upgrade -> downgrade -> upgrade. | `test_migration_0002_round_trips` | Yes |
  | `NeedList.tsx` is under 200 lines and Need row DOM remains regression-safe after split. | `wc -l frontend/src/components/NeedList.tsx` shows 191; `NeedRow.test.tsx` DOM/action regression tests | Yes |
  | Backend pytest and frontend pnpm test pass. | Commands listed above | Yes |

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale
