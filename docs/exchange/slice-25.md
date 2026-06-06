# Slice 25 — Exchange

> Shared channel for **Claude, Codex, ChatGPT, User**.
> Append-only. Communication, NOT commands: a finding becomes Codex work only via a
> User-approved task spec. Each author writes under their own heading; "Open questions"
> and "User — decisions" are shared.
> Commit access: only Codex (its own branch) and the User. ChatGPT and Claude hand their text
> to the User, who commits it.

## Codex — handoff & notes
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

## Claude — conformance review & design notes

## Open questions

## User — decisions

## Claude — final conformance
- [Claude — 2026-06-06] APPROVE — this closes the prompt-editing safety gap: you can now run an unsaved draft against a real model and see actual output before promoting it, which is the difference between editing prompts blind and editing them with feedback. The load-bearing decision is routing the run through complete_model with task="preview" — it means preview inherits cost-ceiling enforcement and call-logging for free and can never drift from the real generation path, while persisting no spec/inspection. Working on draft (unsaved) template text is the whole point and it's honored. Driving the variable fields from a contracts endpoint (rather than hard-coding per-task vars in the UI) keeps the frontend honest against the backend's REQUIRED_VARIABLES_BY_TASK. The 502 gateway-failure mapping was a sound un-specified addition. The one nit (placeholder exchange line) is fixed in the merge commit. Two concerns logged + deferred: preview call_logs don't record the original prompt task (preview-for-generation vs -inspection) for future cost/audit breakdown; and "use a real Need/Spec as sample input" is a later UX nicety (samples are local examples now). Clear to merge.
