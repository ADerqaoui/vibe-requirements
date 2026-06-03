# Slice 18 — V-model navigator: layer selection + layer-aware prompts

Branch: `slice-18` (from `main`). Scope: light up the dormant `layers` / `layer_parents` / `prompts.layer_id` machinery. When generating child specs, the user picks the target V-model layer (constrained to allowed children per `layer_parents`); specs are tagged with that layer instead of the hardcoded `"System Requirement"`; the spec tree shows each spec's layer; and prompt lookup becomes layer-aware (falling back to the layer-NULL prompt when no layer-specific variant exists). **Schema-free** — `layers`, `layer_parents`, `prompts.layer_id`/`discipline_scope`, and `specs.layer_id` all already exist and are seeded.

## In scope

1. **Layer-aware prompt lookup** — extend `prompt_service.get_active(db, task, layer_id=None, discipline_scope=None)`:
   - Among `enabled=1` rows for the task, a row is a candidate if `(row.layer_id == layer_id OR row.layer_id IS NULL)` AND `(row.discipline_scope == discipline_scope OR row.discipline_scope IS NULL)`.
   - Specificity score per candidate: `+2` if `row.layer_id == layer_id` (and not null), `+1` if `row.discipline_scope == discipline_scope` (and not null).
   - Pick the highest score; tie-break by highest `version`, then highest `id`. The `(NULL, NULL)` row always matches as the score-0 fallback.
   - **Backward compatible**: `get_active(db, task)` with no layer behaves exactly as today (returns the NULL/NULL active row).
   - `render(db, task, layer_id=None, discipline_scope=None, **vars)` threads these through to `get_active`.

2. **Layers read API** (`app/api/layers.py`, new):
   - `GET /api/layers` — all layers `(id, name, kind, discipline, sort_order)` ordered by `sort_order`.
   - `GET /api/layers/allowed-children?parent_kind=need` — layers permitted as children of a Need (per `layer_parents` rows whose parent is the Need root).
   - `GET /api/layers/allowed-children?parent_layer_id=N` — layers permitted as children of layer N (per `layer_parents` rows whose parent is layer N's name).
   - Exactly one of `parent_kind` / `parent_layer_id` required → 400 if neither or both; 404 if `parent_layer_id` unknown.

3. **Generation honors target layer** — `generate_for_parent` (and `generate_specs_for_need`) accept `target_layer_id`:
   - Validate server-side that `target_layer_id` is in the allowed-children set for the parent; else 422 `{ error: "layer_not_allowed_for_parent", ... }`. Never trust the client.
   - Created child specs get `layer_id = target_layer_id` (replace the `DEFAULT_SPEC_LAYER` hardcode).
   - Pass `target_layer_id` into `prompt_service.render(...)` so a layer-specific generation prompt is used when one exists (else NULL fallback — no behavior change today).
   - The generate request schema gains `target_layer_id`: required for Spec→child; for Need→spec, default to the single allowed child when exactly one exists (System Requirement per seed), else required.

4. **Classification + inspection layer pass-through** — both operate on an existing spec that already has a `layer_id`. Pass that spec's `layer_id` into `prompt_service.render(...)` so layer-specific classify/inspect prompts apply when present (else NULL fallback). Internal only; no API change.

5. **Frontend — layer selection + visibility**:
   - In the generation UI, once a parent is selected, fetch allowed children and show a layer `<select>` ordered by `sort_order`. Send `target_layer_id` with the generate request.
   - Default selection: the single allowed child if only one; otherwise the lowest `sort_order`.
   - Show each spec's layer name as a small badge in the spec tree. If the spec-tree response does not already include `layer_id`/`layer_name`, add them to its shape and render the badge.
   - Keep every touched file strictly under 200 lines.

6. **Tests** (deterministic):
   - **prompt_service layer lookup**: insert `(task, NULL, NULL)` v1 plus `(task, layerX, NULL)` v1 → `get_active(task, layerX)` returns the layerX row; `get_active(task, layerY)` falls back to NULL; `get_active(task)` (no layer) returns the NULL row. Discipline case: `(task, NULL, "SW")` is chosen by `get_active(task, None, "SW")` over `(NULL, NULL)`. Highest-version tie-break within the same specificity level.
   - **allowed-children**: from a Need → `{System Requirement}`; from the System Requirement layer → `{System Architecture, SW Requirement, Electronic Requirement, Mechanical Requirement}` (per seed); unknown `parent_layer_id` → 404; missing/both params → 400.
   - **generation**: allowed `target_layer_id` → child specs tagged with it AND `render` called with that `layer_id`; disallowed `target_layer_id` → 422 and nothing created; Need→spec with exactly one allowed child defaults correctly when `target_layer_id` omitted.
   - **classification/inspection**: `render` receives the spec's own `layer_id`.
   - **frontend**: layer dropdown lists allowed children, defaults correctly, and sends `target_layer_id`; spec tree shows the layer badge.

## Out of scope (build NO behavior)
- Editing prompts WITH a layer/discipline target via the UI (a layer dropdown in `PromptEditor`) — deferred to slice 19, which pairs naturally with this.
- Seeding layer-specific prompt variants — the lookup is built and tested via direct row inserts; users get layer variants once the editor supports targeting (slice 19).
- Discipline-driven generation (user choosing a discipline at generation time) — only **layer** is user-selectable this slice; `discipline_scope` is plumbed in the lookup but generation passes `None`.
- Editing the V-model structure / `layer_parents` rules.
- Multi-layer batch generation, Router ON, layer-based filtering or alternate tree views beyond the badge.

## API shapes
- `GET /api/layers` (new); `GET /api/layers/allowed-children` (new, 200/400/404).
- Generate request gains `target_layer_id` (required for Spec→child; defaulted for single-allowed-child Need→spec).
- Spec-tree response includes `layer_id` + `layer_name` (add if not already present).
- No schema migration.

## Suggested file layout (one entity per file, ≤200 lines)
Backend: `app/api/layers.py` (new), `app/services/layer_service.py` (new — allowed-children derivation from `layer_parents`, kept small), `app/schemas/layer.py` (new), extend `prompt_service.get_active`/`render`, extend `generation_service` + its request schema + the generate route, extend `classification_service` + `inspector_service` to pass the spec's `layer_id`, and the spec-tree serializer for `layer_id`/`layer_name`. Tests: `test_layer_service.py`, `test_layers_api.py`, extend `test_prompt_service.py`, `test_generations_api.py` (or `test_generation_service.py`), `test_classification_service.py`, `test_inspector_service.py`, and the spec-tree test.
Frontend: a small `useAllowedChildLayers` hook + a `LayerSelect.tsx`, extend the generation form to include the selector and send `target_layer_id`, extend the spec tree node to render the layer badge, plus `frontend/src/api/layers.ts` + `frontend/src/types/layer.ts`. Tests: `LayerSelect.test.tsx` and additions to the generation panel + spec tree tests.

## Acceptance criteria
- Generating from a Need offers exactly the allowed child layer(s) and tags the new specs with the chosen layer (no longer hardcoded to System Requirement).
- Generating from a Spec offers the allowed child layers for that spec's layer and rejects (422) any disallowed target.
- The spec tree visibly shows each spec's V-model layer.
- `get_active` selects a layer-specific prompt when one exists for the requested layer, and falls back to the layer-NULL prompt otherwise; the no-layer call is unchanged.
- `pnpm test` + `pnpm build` + `pnpm typecheck` + backend `pytest` all green (per the slice-17 checklist addition). Handoff in `docs/exchange/slice-18.md` with acceptance-to-test mapping.

## Constraints
- Schema-free; no migration. Backward-compatible `get_active` (the no-layer call must behave exactly as before). Validate `target_layer_id` against `layer_parents` server-side — never trust the client. Do not change the V-model seed rules. `str.format` only. Generation passes `discipline_scope=None` this slice (lookup supports it, UI does not expose it yet). One branch, one PR, no self-merge.
