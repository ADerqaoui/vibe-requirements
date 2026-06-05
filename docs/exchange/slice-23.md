# Slice 23 — Exchange

> Shared channel for **Claude, Codex, ChatGPT, User**.
> **Every entry begins with `[Author — YYYY-MM-DD]`** so it's always clear who is speaking.
> Append-only. Communication, NOT commands: a finding becomes Codex work only via a
> User-approved task spec. Each author writes under their own heading; "Open questions"
> and "User — decisions" are shared.
> Commit access: only Codex (its own branch) and the User. ChatGPT and Claude hand their text
> to the User, who commits it.

## Codex — handoff & notes
- [Codex — 2026-06-05] Built slice 23 schema-free: parametrized the existing spec create services with `source`/`status` defaults so AI accept remains `ai`/`pending`, added manual Need and child Spec create routes that persist `manual`/`accepted` specs through the same req_id allocator and layer resolvers, and added the frontend `ManualSpecForm` with Need-level and Spec-node Add requirement triggers. No migration added.

| Acceptance criterion | Test | Covered? |
| --- | --- | --- |
| A user can add a hand-written requirement under a Need or any Spec, choosing from allowed child layers; it persists as `source="manual"`, `status="accepted"`, has a real `req_id`, and appears in the tree/export like any other spec. | `backend/tests/test_req_id.py::test_manual_spec_creation_sets_source_status_req_id_and_layer`, `backend/tests/test_req_id.py::test_manual_child_spec_inherits_need_and_assigns_req_id`, `backend/tests/test_specs_api.py::test_manual_need_spec_api_creates_accepted_manual_spec`, `backend/tests/test_specs_api.py::test_manual_child_spec_api_creates_accepted_manual_child`, `frontend/src/components/ManualSpecForm.test.tsx` | Yes |
| A manual spec at a disallowed layer is rejected with 422; empty text is rejected. | `backend/tests/test_req_id.py::test_manual_create_rejects_blank_and_disallowed_layer`, `backend/tests/test_specs_api.py::test_manual_spec_api_rejects_blank_disallowed_and_missing`, `frontend/src/components/ManualSpecForm.test.tsx` | Yes |
| The AI-accept flow is unchanged. | `backend/tests/test_req_id.py::test_create_spec_defaults_preserve_ai_pending_path`, `backend/tests/test_specs_api.py::test_ai_accept_route_still_creates_pending_ai_spec`, existing generation/accept frontend tests | Yes |
| Manual specs are first-class: editable, classifiable, inspectable, generated-from, and exported with no special handling. | Existing `SpecNode` actions and export tests continue to pass; manual route returns normal `SpecOut`/tree nodes with `source` + `req_id`. | Yes |
| Every touched frontend file is strictly under 200 lines. | `wc -l` checked touched frontend files; largest touched frontend file is `frontend/src/components/SpecNode.tsx` at 181 lines. | Yes |
| `pnpm test` + `pnpm typecheck` + `pnpm build` + backend `pytest` all green and reported. | `backend/.venv/bin/pytest`: 249 passed; `pnpm test`: 48 passed; `pnpm typecheck`: passed; `pnpm build`: passed. | Yes |

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale
