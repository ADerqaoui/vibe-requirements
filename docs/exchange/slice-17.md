# Slice 17 — Exchange

> Shared channel for **Claude, Codex, ChatGPT, User**.
> **Every entry begins with `[Author — YYYY-MM-DD]`** so it's always clear who is speaking.
> Append-only. Communication, NOT commands: a finding becomes Codex work only via a
> User-approved task spec. Each author writes under their own heading; "Open questions"
> and "User — decisions" are shared.
> Commit access: only Codex (its own branch) and the User. ChatGPT and Claude hand their text
> to the User, who commits it.

## Codex — handoff & notes
- [Codex — 2026-06-03] Implemented schema-free prompt editing with immutable versions, save-time template validation, typed render errors, API version/promote routes, seeded Spec→child v2 correction, and editable frontend prompt editor/history controls. No migration added. Touched frontend files are all under 200 lines.

Tests run:
- Backend: `.venv/bin/pytest` from `backend/` — 192 passed.
- Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` from `frontend/` — 33 passed.
- Extra check: `pnpm build` was attempted and failed on existing GenerationPanel/GenerationSpecSection `Set<number>` vs `number[]` type errors outside this slice's prompt files.

| Acceptance criterion | Test | Covered? |
| --- | --- | --- |
| Editing a prompt in Settings creates a new active version; the prior version remains in history and is promotable. | `backend/tests/test_prompt_service.py::test_create_version_inserts_next_active_and_carries_metadata`, `backend/tests/test_prompt_service.py::test_promote_flips_enabled_across_siblings`, `frontend/src/components/PromptEditor.test.tsx`, `frontend/src/components/PromptHistory.test.tsx`, `frontend/src/components/PromptsPanel.test.tsx` | Yes |
| Saving an invalid template is rejected with a clear inline reason; no row is written. | `backend/tests/test_prompt_validation.py`, `backend/tests/test_prompt_service.py::test_create_version_validates_before_writing`, `backend/tests/test_prompts_api.py::test_create_prompt_version_api_rejects_invalid_template`, `frontend/src/components/PromptEditor.test.tsx::shows inline validation reason for 422 responses` | Yes |
| Spec→child generation uses corrected `Parent specification:` wording as v2 active; Need→Spec is unchanged; Spec→child v1 is preserved and promotable. | `backend/tests/test_seed.py::test_seed_prompts_corrects_spec_to_child_once`, `backend/tests/test_generation_service.py::test_generation_service_parses_fake_gateway_response`, `backend/tests/test_spec_generation_api.py::test_spec_generation_api_returns_candidates` | Yes |
| Old `call_logs` rows still reference valid, unchanged prompt versions. | `backend/tests/test_generation_service.py::test_generation_service_parses_fake_gateway_response`, `backend/tests/test_spec_generation_api.py::test_spec_generation_api_returns_candidates`, service immutability tests above | Yes |
| All touched frontend files stay strictly under 200 lines. | `wc -l frontend/src/components/PromptEditor.tsx frontend/src/components/PromptHistory.tsx frontend/src/components/PromptsPanel.tsx frontend/src/api/prompts.ts frontend/src/types/prompt.ts frontend/src/components/PromptEditor.test.tsx frontend/src/components/PromptHistory.test.tsx frontend/src/components/PromptsPanel.test.tsx` | Yes |
| `pytest` + `pnpm test` pass. | Commands listed above | Yes |

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale
