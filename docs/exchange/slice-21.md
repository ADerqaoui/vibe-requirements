# Slice 21 — Exchange

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
- [Codex — 2026-06-05] Built slice 21 schema-free: prompt variants are keyed by `(task, layer_id, name)`, defaults are stored in the `prompt_defaults` settings JSON map, and version/create/promote/list/default lookup are variant-scoped. Added `select_prompt` with the future context seam and threaded optional `prompt_id` through generation and inspection. Added variant list/set-default APIs and frontend prompt selectors for generation, inspection, and the prompts panel. Router mode omits prompt selection and uses the default.

| Acceptance criterion | Test | Covered? |
| --- | --- | --- |
| A `(task, layer)` can hold several named prompt variants at once; one is the default; the panel shows which. | `backend/tests/test_prompt_service.py::test_variant_isolation_for_create_promote_and_next_version`, `backend/tests/test_prompts_api.py::test_prompt_variants_api_lists_creates_and_sets_default`, `frontend/src/components/PromptsPanel.test.tsx` | Yes |
| At generation/inspection you can pick a variant; router uses the default automatically and UI shows which prompt ran. | `backend/tests/test_generation_service.py::test_generation_service_uses_explicit_prompt_variant`, `backend/tests/test_inspector_service.py::test_inspector_service_uses_explicit_prompt_variant`, `backend/tests/test_generations_api.py`, `backend/tests/test_inspections_api.py`, `frontend/src/components/GenerationPanel.test.tsx`, `frontend/src/components/SpecList.test.tsx`, `frontend/src/App.test.tsx` | Yes |
| Changing the default for a layer takes effect immediately and is used when none is explicitly chosen. | `backend/tests/test_prompt_service.py::test_default_variant_controls_get_active_with_fallback`, `backend/tests/test_prompts_api.py::test_prompt_variants_api_lists_creates_and_sets_default`, `frontend/src/components/PromptsPanel.test.tsx` | Yes |
| Old `call_logs` still reference valid unchanged versions; immutability holds. | `backend/tests/test_generation_service.py`, `backend/tests/test_inspections_api.py`, `backend/tests/test_prompt_slot_versioning.py` | Yes |
| Backward compatible with one variant per group. | Existing prompt lookup/versioning/generation/inspection suites, including `backend/tests/test_prompt_layer_lookup.py` and `backend/tests/test_prompt_slot_versioning.py` | Yes |
| Every touched frontend file is strictly under 200 lines. | `wc -l` checked touched frontend files; largest is `frontend/src/hooks/useGenerationActions.ts` at 199 lines. | Yes |
| `pytest`, `pnpm test`, `pnpm typecheck`, and `pnpm build` are green. | `backend/.venv/bin/pytest` from `backend/`: 230 passed; `pnpm test`: 43 passed; `pnpm typecheck`: passed; `pnpm build`: passed. | Yes |

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale
