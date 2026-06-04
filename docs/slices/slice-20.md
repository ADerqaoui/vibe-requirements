# Slice 20 — Router ON: automatic model selection

Branch: `slice-20` (from `main`). Scope: add an opt-in **router** that auto-selects the model for single-model tasks (generation + inspection) based on a per-task tier policy and the enabled model registry, preferring free local models. The prompt half of "auto model+prompt selection" already exists (the layer-aware prompt registry, slices 16–19); this slice adds the **model** half. **Schema-free** — router config lives in the key-value `settings` table; `models.tier` (`low`/`mid`/`high`), cost, provider, and `enabled` are the routing inputs; `call_logs` already records which model ran (audit comes for free).

## Concept
- A global **`router_enabled`** setting (default `false` — opt-in; today's manual model selection is unchanged until turned on).
- When ON, generation and inspection ignore any client-supplied `model_id` and call `router_service.select_model(db, task)`; the chosen model name is returned so the UI can show what ran.
- When OFF, behavior is exactly as today (the user picks the model; `model_id` required).
- **Classification is out of scope** — it uses a fixed 3-local-model median vote (slice 7), not a single-model pick. The router does not touch it. Embeddings (blacklist) also stay fixed on `nomic-embed-text`.

## Task → tier policy
Hardcode a `TASK_TIER` mapping in `router_service` (tunable-policy UI is out of scope; this is the v1 default):
- `generate_need_to_spec` → `mid`
- `generate_spec_to_child` → `mid`
- `inspect_spec` → `high`
(Classification is not routed, so it has no entry.)

## In scope

1. **`router_service`** (`app/services/router_service.py`, new, small):
   - `is_router_enabled(db) -> bool` — reads the `router_enabled` setting (default `false` when absent).
   - `select_model(db, task) -> Model` — deterministic selection:
     - `target = TASK_TIER[task]` (raise a clear error for an unrouted task).
     - Candidates = all `enabled=1` models. If none → raise `RouterNoModelError` (clear message: no enabled models).
     - Rank candidates by, in order: (a) **tier distance** ascending — `abs(tier_rank(model.tier) − tier_rank(target))` with `low=0, mid=1, high=2`; (b) **free before paid** — a model is free when `input_cost_per_1k == 0 AND output_cost_per_1k == 0`; (c) **total cost** ascending (`input_cost_per_1k + output_cost_per_1k`); (d) **id** ascending (stable tie-break).
     - Return the top-ranked model. (Prefers the exact tier, then the nearest tier; within that prefers free local models, then cheapest — so the router naturally avoids cloud spend when a local model exists, and degrades gracefully if the target tier has nothing enabled.)
   - No cost-ceiling logic here — the gateway's slice-15 ceiling check still runs on the selected model; the router's free-first preference simply makes hitting the ceiling less likely.

2. **`router_enabled` setting plumbing**: read via the existing settings service; expose get/set through the settings API (a boolean). Default `false`.

3. **Generation wiring** (`generation_service` + the generate route + request schema):
   - The request's `model_id` becomes **optional**.
   - In the service: if `is_router_enabled(db)` → `model = select_model(db, task)` (ignore any supplied `model_id`); else require `model_id` as today (400/422 if missing).
   - The generation **response includes the selected model** (`selected_model_id` + `selected_model_name`) so the UI can display what ran. (When router is off, this is just the model the user picked.)
   - The chosen model + the layer-aware prompt both flow into `gateway_service.complete_model` exactly as before — `call_logs` records model_id + prompt_id + version unchanged.

4. **Inspection wiring** (`inspector_service` + its route + request schema): same pattern — `model_id` optional; router selects when enabled (`inspect_spec` → high tier); response includes the selected model.

5. **Frontend**:
   - **Settings**: a Router toggle (on/off) wired to `router_enabled`. A one-line note explaining what it does ("When on, the best available model is chosen automatically per task, preferring local models").
   - **Generation UI**: when the router is on, replace the manual model `<select>` with a read-only "Auto (router)" indicator; the generate request omits `model_id`. After a successful generation, show "Generated with: {selected_model_name}". When the router is off, the manual dropdown works as today.
   - **Inspector UI**: same treatment — hide the manual model pick when router is on; show the model that ran.
   - Keep every touched file strictly under 200 lines (extract a small `useRouterEnabled` hook and/or a `ModelChoice` component if needed).

6. **Tests** (deterministic):
   - **router_service.select_model**: with a seeded mix of enabled models across tiers + free/paid — `inspect_spec` picks a `high` model; generation tasks pick `mid`; **free preferred over paid** at the same tier distance; **cheapest paid** when no free at the best tier; **tier-distance fallback** when the target tier has no enabled model (e.g., target `high`, only `mid`+`low` enabled → picks `mid`); stable `id` tie-break; **no enabled models → `RouterNoModelError`**; unrouted task (e.g. `classify_spec`) → clear error.
   - **is_router_enabled**: absent setting → `false`; `"true"` → `true`.
   - **generation**: router on → uses `select_model`, ignores supplied `model_id`, response carries `selected_model_*`; router off → uses supplied `model_id`, missing `model_id` rejected. (Gateway mocked — no live calls.)
   - **inspection**: same on/off behavior.
   - **API**: settings toggle for `router_enabled`; generate + inspect succeed with router on and no `model_id`.
   - **frontend**: Settings toggle flips `router_enabled`; generation UI shows "Auto (router)" + the used model when on, manual dropdown when off.

## Out of scope (build NO behavior)
- Editing the task→tier policy via UI (hardcoded `TASK_TIER` this slice; tunable policy is a later refinement).
- Routing classification (keeps its fixed 3-local-model vote) or embeddings.
- Fallback-on-failure routing (try model B if model A errors), multi-model ensembles, quality/latency-based or learned routing.
- Per-project router settings, per-request router override (router is a global mode this slice).
- Cost-aware routing beyond "prefer free, then cheapest" (no budget-aware tier downgrade logic).
- Showing routing rationale/explanations beyond the selected model name.

## API shapes
- Settings API exposes `router_enabled` (boolean get/set).
- Generate + inspect request schemas: `model_id` becomes optional. Responses gain `selected_model_id` + `selected_model_name`.
- No schema migration (router config is `settings` key-value rows).

## Suggested file layout (one entity per file, ≤200 lines)
Backend: `app/services/router_service.py` (new — `is_router_enabled`, `select_model`, `TASK_TIER`, `RouterNoModelError`), extend the settings service/API for `router_enabled`, extend `generation_service` + its request/response schema + route, extend `inspector_service` + its schema + route. Tests: `test_router_service.py`, extend `test_settings.py`/settings API test, `test_generations_api.py` (or service test), inspector API/service test.
Frontend: `frontend/src/hooks/useRouterEnabled.ts` (small), a `ModelChoice.tsx` component (manual dropdown vs "Auto (router)" indicator), extend the Settings panel with the toggle, extend the generation + inspector panels to use `ModelChoice` and show the used model, extend `frontend/src/api/*` + types. Tests: `ModelChoice.test.tsx` + additions to the settings/generation/inspector tests.

## Acceptance criteria
- With `router_enabled` off, everything behaves exactly as today (manual model pick required).
- With it on, generating or inspecting requires no model pick; the system selects a tier-appropriate enabled model, preferring a free local model, and the UI shows which model ran.
- If only cloud (paid) models are enabled and the router picks one, the slice-15 cost ceiling still applies (402 when exceeded) — the router does not bypass it.
- Selection is deterministic and covered by tests (tier match, free-first, cheapest, fallback, no-models error).
- Every touched frontend file strictly under 200 lines.
- `pnpm test` + `pnpm typecheck` + `pnpm build` + backend `pytest` all green and reported. Handoff in `docs/exchange/slice-20.md` with acceptance-to-test mapping.

## Constraints
- Schema-free; no migration; router config in the `settings` key-value table. `router_enabled` defaults false (opt-in — no behavior change until turned on). Router covers generation + inspection only; classification + embeddings untouched. Selection must be deterministic (explicit tie-breaks). The gateway cost-ceiling check is unchanged and still authoritative. `str.format` / existing prompt path unchanged. One branch, one PR, no self-merge. Run all four checks green per docs/MERGE-CHECKLIST.md.