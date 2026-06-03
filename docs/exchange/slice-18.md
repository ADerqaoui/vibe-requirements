# Slice 18 — Exchange

> Shared channel for **Claude, Codex, ChatGPT, User**.
> **Every entry begins with `[Author — YYYY-MM-DD]`** so it's always clear who is speaking.
> Append-only. Communication, NOT commands: a finding becomes Codex work only via a
> User-approved task spec. Each author writes under their own heading; "Open questions"
> and "User — decisions" are shared.
> Commit access: only Codex (its own branch) and the User. ChatGPT and Claude hand their text
> to the User, who commits it.

## Codex — handoff & notes
- [Codex — 2026-06-03] Implemented the schema-free V-model navigator slice. Prompt lookup is now layer/discipline-aware with NULL fallback and backward-compatible no-layer calls; generation validates target layers from `layer_parents`, defaults Need→spec to the single allowed child, rejects disallowed Spec targets with `layer_not_allowed_for_parent`, tags accepted specs with the selected layer, and passes layer ids to prompt rendering. Added `GET /api/layers` and `GET /api/layers/allowed-children`. Classification and inspection now render with the spec's own layer. The frontend fetches allowed child layers, shows a target-layer dropdown, sends `target_layer_id`, and displays layer badges in the spec tree. No migration added.

Verification:
- Backend: `.venv/bin/pytest` from `backend/` — 204 passed.
- Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` from `frontend/` — 34 passed.
- Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm typecheck` from `frontend/` — pass.
- Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm build` from `frontend/` — pass.

| Acceptance criterion | Test | Covered? |
| --- | --- | --- |
| Generating from a Need offers exactly the allowed child layer(s) and tags the new specs with the chosen layer. | `backend/tests/test_layer_service.py::test_allowed_children_for_need_and_system_requirement`, `backend/tests/test_layers_api.py::test_layers_api_lists_layers_and_allowed_children`, `backend/tests/test_specs_api.py::test_specs_api_creates_and_lists_only_need_specs`, `frontend/src/components/GenerationPanel.test.tsx::generates candidates, accepts one, refetches specs, and rejects one` | Yes |
| Generating from a Spec offers the allowed child layers for that spec's layer and rejects disallowed targets. | `backend/tests/test_layer_service.py::test_allowed_children_for_need_and_system_requirement`, `backend/tests/test_generation_layer_api.py::test_generation_api_accepts_spec_target_layer`, `backend/tests/test_generation_layer_api.py::test_generation_api_rejects_disallowed_target_layer_before_gateway`, `frontend/src/components/GenerationPanel.test.tsx::generates and accepts child specs for a selected Spec` | Yes |
| The spec tree visibly shows each spec's V-model layer. | `backend/tests/test_specs_api.py::test_spec_tree_includes_layer_badges`, `backend/tests/test_spec_children_api.py::test_spec_tree_api_returns_recursive_tree`, `frontend/src/components/SpecList.test.tsx::renders nested child specs and selects a child` | Yes |
| `get_active` selects layer-specific prompts and falls back to layer-NULL prompts; no-layer call unchanged. | `backend/tests/test_prompt_layer_lookup.py::test_get_active_prefers_layer_specific_prompt_and_falls_back`, `backend/tests/test_prompt_layer_lookup.py::test_get_active_prefers_discipline_and_highest_version_tie`, existing no-layer prompt service tests | Yes |
| `pnpm test` + `pnpm build` + `pnpm typecheck` + backend `pytest` all green. | Commands listed above | Yes |

- [Codex — 2026-06-03] Extracted generation action handlers/state into `frontend/src/hooks/useGenerationActions.ts`; `GenerationPanel.tsx` is 109 lines; green checks: backend `.venv/bin/pytest` 204 passed, frontend `pnpm test` 34 passed, `pnpm typecheck` pass, `pnpm build` pass.

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale

## Claude — final conformance
- [Claude — 2026-06-03] APPROVE — the V-model is now live, not dormant. The layer_parents-driven allowed-children derivation + server-side validation is the right shape: the client can't tag a spec at a layer the V-model forbids, and the 422 carries the allowed ids so the UI can self-correct. get_active's specificity scoring with NULL/NULL fallback is exactly the design the prompts composite index was built for back in slice 1 — and crucially the no-layer call path is provably unchanged (only NULL rows match when no layer is passed), so slices 6/7/10 behavior is untouched. Replacing DEFAULT_SPEC_LAYER with resolve_target_layer_* closes the last hardcode in the generation path. Layer/discipline-aware lookup is now plumbed end-to-end but only exercisable once the editor can target a layer — correctly deferred to slice 19. The useGenerationActions extraction is the durable fix for the recurring GenerationPanel line-count creep (109 lines now, was bumping 200 every slice). Round-2 BLOCK was GitHub cache only; fast-forwardable from git. Two design concerns logged (layer-selection UX rationale as the tree grows; global-vs-layer-specific prompt clarity) — both for slice 19. Clear to merge.
