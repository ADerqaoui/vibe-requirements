# Slice 21 — Selectable prompt variants per layer (with the select_prompt seam)

Branch: `slice-21` (from `main`). Scope: let each `(task, layer)` hold **multiple named prompt variants** (e.g. "EARS", "Concise") that coexist as concurrent choices; one is the **default** for that layer; generation uses the default OR an explicitly chosen variant; the router uses the default. All prompt selection flows through a single `select_prompt(db, task, layer_id, context)` chokepoint — the seam that lets a future slice make the router choose by context/constraints without touching the data model, generation flow, or UI. **Schema-free** — the variant key uses the existing `name` column; the per-layer default lives in the `settings` key-value table as a JSON map (no migration, by design — keeps the operational risk low).

## Model
- A **variant** = `(task, layer_id, name)`. Multiple variants can coexist in the same `(task, layer)` **group**. Each variant has immutable **versions** (the `version` field); exactly one enabled version per variant.
- This **refines slice-19's per-`(task, layer)` slot to per-`(task, layer, name)` variant.** Versioning/enabling/promote become variant-scoped (add `name` to the slot key). Backward compatible: today every `(task, layer)` group has exactly one variant, so behavior is unchanged until a second variant is added.
- The **default variant** for a `(task, layer)` group is stored in a single `settings` row, key `prompt_defaults`, value = JSON map `{ "<task>|<layer_id>": "<variant name>" }` (use the literal string `"null"` for the global layer, i.e. `layer_id IS NULL`). When a group has no entry, the default is the group's sole/most-recent variant (deterministic fallback: the variant whose enabled version has the highest version, then id).

## In scope

1. **Variant-scoped versioning** (`prompt_service`): extend the slot key from `(task, layer_id)` to `(task, layer_id, name)`. `_slot_filter`/`_next_version`/`_active_in_slot`/`promote`/`create_version` all become variant-scoped. Creating or promoting a version of variant "EARS" must not touch variant "Concise" in the same group (the same isolation principle as slice 19, one level finer). `create_version(db, task, template, layer_id, name, description)`: `name` now identifies the variant; if the `(task, layer, name)` variant is new, this is its v1; else next version within that variant.

2. **Default management** (`prompt_service` + settings):
   - `get_default_variant_name(db, task, layer_id) -> str | None` — reads the `prompt_defaults` JSON; falls back deterministically (highest enabled version, then id) when unset.
   - `set_default(db, task, layer_id, name)` — validates the variant exists, writes the `prompt_defaults` JSON entry. Exactly one default per group (the map holds one name per key).
   - `get_active(db, task, layer_id=None, discipline_scope=None)` — **now returns the default variant's enabled version** for the best-matching group. Keep the slice-18 specificity fallback (exact layer → global) for choosing the *group*; within the chosen group, pick the *default variant's* enabled version. Backward compatible: one-variant groups resolve exactly as today.

3. **`select_prompt` chokepoint** (`prompt_service`, the seam):
   - `select_prompt(db, task, layer_id, context) -> RenderedPromptRef` where `context` is a small object carrying at least an optional `prompt_id` plus the parent/layer info on hand.
   - Body for this slice: if `context.prompt_id` is set → load that prompt row and use its variant's enabled version (validate it exists/enabled; 404/422 otherwise); else → `get_active(db, task, layer_id)` (the default). **Most of `context` is unused this slice** — it exists so a later slice can select by complexity/constraints without re-threading data. Document this.

4. **Generation + inspection wiring**:
   - Generation request gains an optional `prompt_id`. Generation calls `select_prompt(db, task, layer_id, context={prompt_id, parent, layer})`; renders that variant; passes its `prompt_id` + `version` to `gateway_service.complete_model` (audit unchanged).
   - When the **router is on**, the router does not choose a prompt this slice — `select_prompt` with no `prompt_id` returns the layer default. (Router prompt-choice is a deliberate future extension via the same seam.)
   - Generation response gains `selected_prompt_id` + `selected_prompt_name` (the variant name), alongside the existing `selected_model_*`, so the UI shows which prompt ran.
   - Inspection: same optional-`prompt_id` + default pattern (its task is `inspect_spec`).

5. **API** (extend `app/api/prompts.py`):
   - `GET /api/prompts/{task}/variants?layer_id=<id|absent for global>` — list variants in the group: each with `name`, enabled `version`, `template`, `is_default` (bool), `prompt_id` of the enabled version.
   - `POST /api/prompts/{task}/versions` (slice-19, made variant-aware) — body gains `name` (the variant) alongside `template`/`layer_id`/`description`; targets the `(task, layer, name)` variant (new variant if the name is new). Validation (variable contract, layer-not-Need) unchanged.
   - `POST /api/prompts/set-default` — body `{ task, layer_id, name }` → set the group default. 404 if the variant doesn't exist.
   - `GET /api/prompts` unchanged in shape but now returns the **default** variant per group (one per group).

6. **Frontend**:
   - **Prompts panel**: within each `(task, layer)` group, list the variants with a **"default" badge**, an **"Add variant"** action (new name → new variant), and a **"Set default"** control on non-default variants. (Edit/History from slice 19 now operate per variant.)
   - **Generation UI**: a **prompt-variant dropdown** beside the model dropdown, listing the target layer's variants (default selected); sends the chosen `prompt_id`. When the router is on, the prompt dropdown shows the default as "Auto (default)" and generation omits `prompt_id`. After a successful generation, show "Prompt: {selected_prompt_name}" next to the model used.
   - **Inspector UI**: same prompt-variant dropdown (for `inspect_spec`).
   - Keep every touched file strictly under 200 lines (NeedList.tsx is already at 196 — if threading the variant prop pushes it over, extract; don't exceed).

7. **Tests** (deterministic):
   - **variant isolation**: adding a version to variant "EARS" doesn't disable variant "Concise"; promote is variant-scoped; `_next_version` is per variant.
   - **default**: `set_default` flips the group default (one default per group); `get_default_variant_name` fallback when unset; `get_active` returns the default variant's enabled version; with one variant, behaves exactly as before (backward compat).
   - **select_prompt**: with `prompt_id` → that variant; without → default; unknown/disabled `prompt_id` → typed error → 404/422.
   - **generation/inspection**: explicit `prompt_id` used; omitted → default; response carries `selected_prompt_*`; router-on path returns the default (no `prompt_id`).
   - **API**: list variants (with `is_default`); create-variant via versions endpoint with a new `name`; set-default (+404); generation with `prompt_id`.
   - **frontend**: variant dropdown lists + selects + sends `prompt_id`; "Set default" calls the API and updates the badge; "Add variant" creates a new variant; router-on hides manual prompt pick.

## Out of scope (build NO behavior)
- Router choosing the prompt by context/complexity/constraints (the `select_prompt` seam exists for it; the policy is a later slice).
- `is_default` schema column / any migration (default lives in `settings` JSON this slice).
- Discipline-axis variants (still deferred — `discipline_scope` stays NULL).
- Deleting variants/versions; renaming a variant in place (add a new one + set default instead); per-project prompt sets; prompt preview/test-run (separate future slice); diff view.

## API shapes
- `GET /api/prompts/{task}/variants?layer_id=` (new). `POST /api/prompts/set-default` (new, 200/404). `POST /api/prompts/{task}/versions` gains `name`. Generate + inspect requests gain optional `prompt_id`; responses gain `selected_prompt_id` + `selected_prompt_name`. `GET /api/prompts` returns the default per group. No schema migration.

## Suggested file layout (one entity per file, ≤200 lines)
Backend: extend `prompt_service` (variant-scoped slot key; `get_default_variant_name`/`set_default`; `get_active` picks the default variant; `select_prompt` chokepoint + a small `PromptSelectionContext`); a tiny `prompt_defaults` settings helper (read/write the JSON map); extend `app/schemas/prompt.py` + `app/api/prompts.py`; wire generation + inspector services/schemas/routes. Tests: extend `test_prompt_service.py`, `test_prompts_api.py`, generation + inspector tests.
Frontend: a `PromptVariantSelect.tsx` (dropdown, mirrors `ModelChoice`), extend the Prompts panel for variants + set-default + add-variant, wire the selector into the generation + inspector panels, extend `api/prompts.ts` + types. Extract from `NeedList.tsx`/`PromptsPanel.tsx` if either crosses 200. Tests: `PromptVariantSelect.test.tsx` + panel additions.

## Acceptance criteria
- A `(task, layer)` can hold several named prompt variants at once; one is the default; the panel shows which.
- At generation/inspection you can pick a variant (default preselected); with the router on, the default is used automatically and the UI shows which prompt ran.
- Changing the default for a layer takes effect immediately (no reload) and is the prompt used when none is explicitly chosen.
- Old `call_logs` still reference valid unchanged versions (immutability holds; variants only add rows).
- Backward compatible: with one variant per group, behavior is identical to today.
- Every touched frontend file strictly under 200 lines.
- `pnpm test` + `pnpm typecheck` + `pnpm build` + backend `pytest` all green and reported. Handoff in `docs/exchange/slice-21.md` with acceptance-to-test mapping.

## Constraints
- Schema-free; no migration; default in the `settings` `prompt_defaults` JSON. Variant isolation is the critical invariant — versioning/promote on one variant must never touch another (test it). `get_active` must stay backward compatible for one-variant groups. All prompt selection routes through `select_prompt`; `context` is mostly unused now but threaded for the future. `str.format` unchanged. Router does not pick prompts this slice. One branch, one PR, no self-merge. All four checks green per docs/MERGE-CHECKLIST.md.