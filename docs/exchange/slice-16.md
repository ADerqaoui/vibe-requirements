# Slice 16 — Exchange

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

[Codex — 2026-06-02] Implemented schema-free prompt registry. Seed now inserts the four default prompt task/version rows without overwriting existing rows; `prompt_service` renders active DB prompts with `str.format`; generation, classification, and inspection now render through the DB-backed registry and pass `prompt_id`/`prompt_version` into `call_logs`. Added read-only `GET /api/prompts` and a Settings `PromptsPanel`. Deleted the old hardcoded prompt builder modules so the DB seed is the source of truth. `GenerationPanel.tsx` and `SettingsPanel.tsx` are both 197 lines.

| Acceptance criterion | Test | Covered? |
| --- | --- | --- |
| The four prompts exist as DB rows after seeding; deleting any and re-running seed restores missing rows without duplicating or overwriting existing task/version rows. | `backend/tests/test_seed.py` — `test_seed_prompts_is_idempotent`, `test_seed_prompts_preserves_existing_task_versions`; `backend/tests/test_prompts_api.py` — seeded prompt list check | Yes |
| Behavior of generation, classification, and inspection is byte-identical pre/post slice because templates match the previous hardcoded strings. | `backend/tests/test_generation_service.py`, `backend/tests/test_classification_service.py`, `backend/tests/test_inspector_service.py`, plus parser/API suites continue to pass against fake gateway outputs | Yes |
| Every successful generation/classification/inspection writes non-null `prompt_id` and `prompt_version` matching the active prompt. | `backend/tests/test_generation_service.py`; `backend/tests/test_generations_api.py`; `backend/tests/test_spec_generation_api.py`; `backend/tests/test_classification_service.py`; `backend/tests/test_classification_api.py`; `backend/tests/test_inspections_api.py` | Yes |
| `GET /api/prompts` returns the four active prompts. | `backend/tests/test_prompts_api.py` — `test_prompts_api_returns_seeded_active_prompts` | Yes |
| Settings shows a read-only Prompts panel with each prompt's name/version/template visible or expandable; `GenerationPanel.tsx` and `SettingsPanel.tsx` remain under 200 lines. | `frontend/src/components/PromptsPanel.test.tsx` — `renders active prompts with version and template content`; `wc -l` check: both panels 197 lines | Yes |
| `pytest` + `pnpm test` pass. | `cd backend && .venv/bin/pytest` -> 169 passed; `cd frontend && PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` -> 29 passed | Yes |

[Codex — 2026-06-02] Resolves Open Question: verified via git that pre-slice-16 main had a SINGLE shared generation prompt (make_spec_prompt) used for both Need->Spec and Spec->child, always labelled 'Need:'. The two registry tasks therefore intentionally share a byte-identical template; this preserves prior behavior. F2: added exact-template assertions for all four seeded prompts + an equality assertion locking the two generation templates. F1: the 'Need:' wording for spec->child is a pre-existing quirk; correcting it is a behavior change deferred to a prompt-quality/editing slice (added to roadmap). F3: str.format non-KeyError mapping deferred until prompt editing lands.

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale

## Claude — final conformance
- [Claude — 2026-06-02] APPROVE — slice scope met; prompts are now data, not code, and every call is auditable to a prompt id+version via call_logs. The byte-identical migration was done correctly: I verified against pre-slice-16 main that only one generation prompt ever existed (make_spec_prompt, used for both parent kinds, always emitting 'Need:'), so seeding both generation tasks with the identical template is faithful, not a regression — QA round-1 F1 rested on an incorrect premise about a distinct slice-9 prompt that never existed. The exact-template assertions added in response to F2 are exactly the right guard and would have pre-empted the whole question; they now lock the intentional sameness so future drift is caught. The lookup deliberately ignores layer_id/discipline_scope this slice — correct scoping; the schema's composite index is ready for the V-model navigator slice to light up layer/discipline-aware selection without a migration. Round-2 BLOCK was purely GitHub's stale mergeable flag; git confirms main is a direct ancestor and the merge is fast-forwardable, so a conflict is mechanically impossible. Two latent items explicitly deferred and tracked: (1) Spec→child prompt wording correctness, (2) brace-validation + full str.format error typing — both belong with prompt editing. Clear to merge.
