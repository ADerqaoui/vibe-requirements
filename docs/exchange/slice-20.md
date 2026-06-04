# Slice 20 — Exchange

> Shared channel for **Claude, Codex, ChatGPT, User**.
> **Every entry begins with `[Author — YYYY-MM-DD]`** so it's always clear who is speaking.
> Append-only. Communication, NOT commands: a finding becomes Codex work only via a
> User-approved task spec. Each author writes under their own heading; "Open questions"
> and "User — decisions" are shared.
> Commit access: only Codex (its own branch) and the User. ChatGPT and Claude hand their text
> to the User, who commits it.

## Codex — handoff & notes
- [Codex — 2026-06-04] Implemented slice 20 schema-free.
  - Added `router_enabled` setting support and `router_service.select_model` with deterministic tier-distance/free-first/cheapest/id ranking.
  - Generation and inspection now accept optional `model_id`; router-on mode ignores supplied IDs and selects automatically, while router-off mode still requires a manual model.
  - Generation and inspection responses include `selected_model_id` and `selected_model_name`; gateway calls still use `complete_model`, so cost ceiling and call-log audit remain authoritative.
  - Frontend Settings includes the Router toggle, generation and inspection use `ModelChoice`, router mode omits `model_id`, and successful calls show the selected model.
  - Touched frontend files are under 200 lines.

  Tests run:
  - Backend: `.venv/bin/pytest` — 224 passed.
  - Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` — 16 files / 41 tests passed.
  - Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm typecheck` — passed.
  - Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm build` — passed.

  | Acceptance criterion | Test | Covered? |
  | --- | --- | --- |
  | With `router_enabled` off, manual model pick is required and behavior is unchanged. | `backend/tests/test_generation_service.py::test_resolve_generation_model_manual_requires_model_id`; `backend/tests/test_inspector_service.py::test_resolve_inspector_model_manual_requires_model_id`; existing generation/inspection API tests. | Yes |
  | With router on, generate/inspect require no model pick; selected model is tier-appropriate, free-first, and shown in UI. | `backend/tests/test_router_service.py`; `backend/tests/test_generations_api.py::test_generation_api_router_on_ignores_model_id_and_reports_selected_model`; `backend/tests/test_inspections_api.py::test_inspection_api_router_on_ignores_model_id_and_reports_selected_model`; `frontend/src/components/GenerationPanelRouter.test.tsx`; `frontend/src/components/SpecListRouter.test.tsx`. | Yes |
  | Router-selected paid cloud models still obey the slice-15 cost ceiling. | `backend/tests/test_generation_cost_api.py::test_generation_api_cost_ceiling_returns_402`; existing gateway/inspection cost-ceiling tests. | Yes |
  | Selection is deterministic and covers tier match, free-first, cheapest, fallback, no-models, and unrouted-task errors. | `backend/tests/test_router_service.py`. | Yes |
  | Every touched frontend file is strictly under 200 lines. | Manual `wc -l` check across touched frontend files. | Yes |
  | `pnpm test`, `pnpm typecheck`, `pnpm build`, and backend `pytest` are green and reported. | Commands listed above. | Yes |

- [Codex — 2026-06-04] Fixed QA F1/F2/F3 without backend behavior changes.
  - Router state is now fetched once at App level and passed into Settings, generation, and inspection surfaces; Settings toggles update the shared state so already-mounted panels switch immediately.
  - Removed per-panel router-setting reads from GenerationPanel and SpecList.
  - `useRouterEnabled` now calls `onError(error)` before falling back to `false`.
  - Added `frontend/src/App.test.tsx` high-level toggle-flow coverage: router off starts with manual generation/inspection model controls, toggling on switches both mounted surfaces to `Auto (router)` and omits `model_id`, toggling off restores manual controls.

  Tests run:
  - Backend: `.venv/bin/pytest` — 224 passed.
  - Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` — 17 files / 42 tests passed.
  - Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm typecheck` — passed.
  - Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm build` — passed.

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale

## Claude — final conformance
- [Claude — 2026-06-04] APPROVE — the model half of "auto model+prompt selection" is done, mirroring the prompt registry's role for prompts. select_model's ranking is the right shape: exact tier first, nearest tier as graceful fallback, free-local preferred over paid (so the router naturally avoids cloud spend), deterministic id tie-break. Keeping the gateway path unchanged means the cost ceiling and call_logs audit remain authoritative over whatever the router picks — correct layering. Scoping classification + embeddings out is right (the 3-model vote isn't a single-model pick). The QA-round-1 reactivity bug was real and worth the block: a Settings toggle that needs a page reload to take effect is a footgun; lifting router_enabled to app-level shared state is the correct fix and reuses the slice-15 app-coordination precedent rather than inventing new machinery, and the App-level toggle-flow test now locks it. Two design concerns logged (routing-rationale visibility; global-vs-per-project router) — both correctly deferred. NeedList.tsx at 196 is the next extraction candidate. Round-2 BLOCK was GitHub cache only. Clear to merge.
