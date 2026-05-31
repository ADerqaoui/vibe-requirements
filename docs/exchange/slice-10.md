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

- [Codex — 2026-05-31] Applied slice 10 follow-up fixes from QA.

  Built:
  - Added top-level `summary` to `SpecInspectionOut` and mapped it from `spec_inspections.summary`.
  - Extended inspection API tests to assert exact response keys: `id`, `spec_id`, `model_id`, `findings`, `summary`, `passes`, `created_at`.
  - Aligned `latest_inspection_ids` ordering with `GET /api/specs/{id}/inspections`: `created_at DESC, id DESC`, first row per Spec.
  - Added coverage proving spec-tree `latest_inspection_id` matches the first row returned by the newest-first inspections list.
  - No schema changes.

  Verification:
  - `.venv/bin/pytest` from `backend/`: 102 passed, 74 warnings.

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — 2026-05-31] BLOCK — concur with ChatGPT on F1. The slice spec called for top-level `summary` in `SpecInspection`; the persistence is correct (spec_inspections.summary column) but the serializer omitted the field, nesting it under findings.summary instead. Real API contract mismatch. F2 covered by the same followup (response-shape test). F3 (latest_inspection_ids using max(id) vs the list endpoint using created_at) is a real consistency risk — cheap to align. Rulings: F4 / DC1 lifecycle mutability deferred to a future "lifecycle policy + audit-history" slice (paired with spec_revisions and prompt-registry); v1 free transitions acceptable for a single-user LAN tool. DC2 (findings JSON schema versioning) deferred until findings export lands. Followup task issued: summary field, mapping, response-shape test, latest-inspection ordering alignment. No schema change.

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale

## Claude — final conformance
- [Claude — 2026-05-31] APPROVE — F1 (top-level summary), F2 (response-shape test), F3 (latest_inspection_ids ordering aligned with the list endpoint by created_at DESC, id DESC) all resolved. Migration 0002 round-trips cleanly; STRICT + ON DELETE CASCADE on spec_id correctly bound to the parent Spec lifecycle. Inspector service correctly fails closed (no spec_inspections row on gateway failure or parser-empty). NeedList split landed at 191 lines (under 200 target) without DOM regression. F4 / DC1 lifecycle mutability deferred to a future audit-history slice (decisions become immutable-with-history once spec_revisions persistence lands); v1 free transitions acceptable for the single-user LAN context. DC2 findings JSON schema versioning parked for findings-export. Clear to merge.
