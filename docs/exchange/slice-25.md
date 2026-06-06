# Slice 25 — Exchange

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
- [Codex — 2026-06-05] Built slice 25 prompt preview/test-run. Added schema-free `POST /api/prompts/preview` with validate -> render -> `complete_model(task="preview")`, standard 422/402 behavior, no spec/inspection persistence, and call-log cost accounting. Added `GET /api/prompts/contracts` from `REQUIRED_VARIABLES_BY_TASK`. Added `PromptPreviewPanel` to the prompt editor, driven by contracts, posting the current draft template with variable examples and optional model selection, then displaying rendered prompt, output, and cost.

| Acceptance criterion | Test | Covered? |
| --- | --- | --- |
| Editor can enter sample values, run the current draft template, and see rendered prompt, output, and cost without saving | `frontend/src/components/PromptPreviewPanel.test.tsx::renders fields by task and runs the current draft template`; `backend/tests/test_prompt_preview.py::test_prompt_preview_returns_rendered_output_cost_and_logs` | Yes |
| Preview creates no spec or inspection | `backend/tests/test_prompt_preview.py::test_prompt_preview_does_not_create_specs_or_inspections` | Yes |
| Invalid template is rejected with reason | `backend/tests/test_prompt_preview_errors.py::test_prompt_preview_rejects_invalid_template`; `frontend/src/components/PromptPreviewPanel.test.tsx::shows invalid template reasons inline` | Yes |
| Missing/empty required variable is rejected with reason | `backend/tests/test_prompt_preview_errors.py::test_prompt_preview_rejects_missing_variable_value` | Yes |
| Over-budget paid preview returns standard 402 and preview cost counts toward monthly ceiling | `backend/tests/test_prompt_preview_errors.py::test_prompt_preview_cost_ceiling_returns_402`; `backend/tests/test_prompt_preview.py::test_prompt_preview_returns_rendered_output_cost_and_logs` | Yes |
| Omitted `model_id` uses routed/default model | `backend/tests/test_prompt_preview.py::test_prompt_preview_omitted_model_uses_routed_model` | Yes |
| Contracts endpoint returns required variables per task | `backend/tests/test_prompt_preview.py::test_prompt_contracts_endpoint` | Yes |
| Every touched frontend file is under 200 lines | `wc -l frontend/src/components/PromptPreviewPanel.tsx frontend/src/components/PromptPreviewPanel.test.tsx frontend/src/components/PromptEditor.tsx frontend/src/components/PromptEditor.test.tsx frontend/src/api/prompts.ts frontend/src/types/prompt.ts` | Yes |

Tests run:
- Backend: `.venv/bin/pytest` from `backend/` -> 261 passed.
- Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` -> 21 files / 51 tests passed.
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
