# Slice 22 — Exchange

> Shared channel for **Claude, Codex, ChatGPT, User**.
> **Every entry begins with `[Author — YYYY-MM-DD]`** so it's always clear who is speaking.
> Append-only. Communication, NOT commands: a finding becomes Codex work only via a
> User-approved task spec. Each author writes under their own heading; "Open questions"
> and "User — decisions" are shared.
> Commit access: only Codex (its own branch) and the User. ChatGPT and Claude hand their text
> to the User, who commits it.

## Codex — handoff & notes
- [Codex — 2026-06-05] Built slice 22: added the single nullable `specs.req_id` migration, code-side REQ layer abbreviations, per-project/per-layer ID assignment on spec creation, idempotent seed backfill for missing IDs, text-only PATCH editing that flips `source` to `manual`, `req_id` + `source` serialization for SpecOut/tree, Markdown export ID prefixes, and inline frontend editing with req/source badges. Edit history remains deferred per slice scope.

| Acceptance criterion | Test | Covered? |
| --- | --- | --- |
| Every spec — newly generated and pre-existing after seed backfill — has a stable `REQ-<LAYER>-<NNNN>` ID visible in the tree and export. | `backend/tests/test_req_id.py`, `backend/tests/test_specs_api.py::test_spec_tree_includes_layer_badges`, `backend/tests/test_export_markdown.py`, `frontend/src/components/SpecNode.test.tsx` | Yes |
| A user can edit a spec's text in-place; source flips to Manual; `req_id` does not change. | `backend/tests/test_specs_api.py::test_specs_api_edits_text_and_preserves_identity`, `backend/tests/test_req_id.py::test_req_id_is_stable_across_text_edit`, `frontend/src/components/SpecNode.test.tsx`, `frontend/src/components/SpecEditor.test.tsx` | Yes |
| IDs are sequential per `(project, layer)` and never reassigned. | `backend/tests/test_req_id.py::test_req_id_assignment_sequences_per_project_and_layer`, `backend/tests/test_req_id.py::test_seed_backfill_assigns_missing_req_ids_idempotently` | Yes |
| Migration is a clean nullable-column add; backfill is idempotent and runs via seed. | `backend/tests/test_migration_0003.py`, `backend/tests/test_req_id.py::test_seed_backfill_assigns_missing_req_ids_idempotently` | Yes |
| Every touched frontend file is strictly under 200 lines. | `wc -l` checked touched frontend files; largest touched frontend file is `frontend/src/components/SpecNode.tsx` at 198 lines. | Yes |
| `pnpm test` + `pnpm typecheck` + `pnpm build` + backend `pytest` all green and reported. | `backend/.venv/bin/pytest`: 241 passed; `pnpm test`: 46 passed; `pnpm typecheck`: passed; `pnpm build`: passed. | Yes |

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale
