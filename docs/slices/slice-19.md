# Slice 19 — Layer-targeted prompt editing (per-slot versioning)

Branch: `slice-19` (from `main`). Scope: let users author layer-specific prompt variants through the UI, completing the layer-aware lookup built in slice 18 (currently dormant because no UI can create a non-global prompt). Versioning becomes **per-slot** — `(task, layer_id)` — so a layer-specific variant coexists with the global prompt instead of replacing it. The Prompts panel visibly distinguishes global vs layer-specific prompts (addresses ChatGPT slice-18 DC2). **Schema-free.** Discipline-axis targeting stays deferred (generation does not yet request a discipline; authoring discipline-scoped prompts would be dormant — see Out of scope).

## Key model change: per-slot versioning
- A **slot** = `(task, layer_id)` (with `discipline_scope` staying NULL this slice). Each slot holds N immutable versions; exactly one enabled per slot.
- `get_active` (slice 18) is **UNCHANGED** — it already scores all enabled rows by specificity and falls back to the global (NULL-layer) slot. Per-slot enabling just means each slot contributes its single enabled row as a candidate.
- `create_version` + `promote` change their "disable siblings" scope from per-task to **per-slot**:
  - `create_version(db, task, template, layer_id=None, name=None, description=None)`: `version = max(version WHERE task = task AND layer_id IS [target]) + 1` (a brand-new slot starts at v1); insert `enabled=1`; disable the prior enabled row **in the same slot only**. Creating a `(task, layerX)` variant MUST NOT disable the `(task, NULL)` global prompt.
  - `promote(db, prompt_id)`: enable the row; disable other enabled rows **in the same slot** (same `task` AND same `layer_id`) only.
- **Backward compatible**: existing global prompts are the `(task, NULL)` slot; all slice-17/18 behavior for them is unchanged. With no variants created, `GET /api/prompts` still returns the same 4 active prompts.

## In scope

1. **Per-slot versioning** in `prompt_service` (`create_version` + `promote` scoped to `(task, layer_id)`). When `layer_id` is provided to `create_version`, the new version belongs to that layer's slot with that `layer_id` (NOT carried over from the global active). When omitted, behaves as today (global slot; carry over the active global's `name`/`description`).

2. **`layer_id` on the create API**: `PromptVersionCreate` gains `layer_id: int | None = None`. `POST /api/prompts/{task}/versions` validates: if `layer_id` is given, the layer must exist (404/422) and must NOT be the root `"Need"` layer (422 — specs are never authored at Need). The per-task variable-contract validation (slice 17) is unchanged (layer does not change required variables).

3. **`list_active` returns one active prompt per SLOT** (all `enabled=1` rows), ordered by task, then by layer `sort_order` with the global (NULL-layer) row first within each task. This lets the panel render global + variants. (Slice-17 `list_active` returned one per task; now one per slot. With only global prompts seeded, the result is the same 4 rows — existing API tests still pass.)

4. **`list_versions(task)`** returns all versions across all slots for the task, each carrying `layer_id` + `layer_name` + `enabled`, ordered by layer (global first) then `version` desc — so the frontend can group history by slot. `promote(id)` derives the slot from the row.

5. **Frontend**:
   - `PromptsPanel`: list active prompts grouped by task; within a task show the **Global** prompt and each layer-specific variant, each clearly labeled with its scope ("Global" vs the layer name). Each entry has Edit + History/promote. Add an **"Add layer variant"** action per task.
   - **Add layer variant**: opens `PromptEditor` with a layer `<select>` (from `GET /api/layers`, excluding `"Need"`, ordered by `sort_order`), template prefilled from the task's global active prompt; Save → `POST` with `layer_id`. Show inline 422 reason on invalid template/layer.
   - **Edit** on an existing prompt: creates a new version in the SAME slot; the scope (Global or the layer name) is shown as a read-only label, NOT editable (changing scope = creating a different variant, which is the Add-variant flow).
   - Keep every touched file strictly under 200 lines (per the merge checklist). Extract the layer picker / variant flow into a small component or hook if `PromptEditor` or `PromptsPanel` would otherwise cross 200.

6. **Tests** (deterministic):
   - **slot isolation** (the crux): `create_version(task, layerX)` creates `(task, layerX)` v1 enabled WITHOUT disabling `(task, NULL)` global → `get_active(task, layerX)` returns the variant; `get_active(task, otherLayer)` returns global; `get_active(task)` returns global. A second `create_version(task, layerX)` → `(task, layerX)` v2, disables v1 of THAT slot only, global untouched. `promote` an older `(task, layerX)` version → only that slot's enabled flips; global + other slots untouched.
   - **validation**: `layer_id` for a non-existent layer rejected; `layer_id == Need` rejected (422); invalid template still rejected per the slice-17 contract.
   - **list_active**: returns one per slot (global + variants) in the correct order; with no variants, exactly the 4 globals.
   - **list_versions**: groups across slots with `layer_id`/`layer_name`; ordering correct.
   - **API**: `POST` with `layer_id` success (200) + invalid layer (422) + Need layer (422); existing global `POST` still works.
   - **frontend**: Add-variant flow shows the layer picker and posts `layer_id`; panel labels Global vs layer variants distinctly; Edit shows scope read-only.

## Out of scope (build NO behavior)
- Discipline-axis targeting in the editor — generation/classification/inspection do not request a discipline yet, so a discipline-scoped prompt would never be selected. Deferred until either discipline-aware generation or derive-discipline-from-layer lands. `discipline_scope` stays plumbed in the service/lookup but unused and NULL for all authored prompts.
- Prompt preview/test-run (not selected this round — a separate future slice).
- Deleting prompt versions or slots.
- Per-project prompt overrides.
- Changing a prompt's scope in place (use Add-variant instead).
- Editing the V-model / layers themselves.
- Router ON.

## API shapes
- `PromptVersionCreate` gains `layer_id?: int`. `POST /api/prompts/{task}/versions` accepts it (200/422/404).
- `GET /api/prompts` now returns one active per slot (was one per task) — frontend groups by task.
- `GET /api/prompts/{task}/versions` includes `layer_id` + `layer_name` per row.
- `GET /api/layers` (slice 18) reused for the picker.
- No schema migration.

## Suggested file layout (one entity per file, ≤200 lines)
Backend: extend `prompt_service.create_version`/`promote`/`list_active`/`list_versions` for per-slot logic; extend `app/schemas/prompt.py` (`PromptVersionCreate.layer_id`, `layer_name` on version-read); extend `app/api/prompts.py` (validate layer exists + not Need); a tiny helper to resolve `layer_name` for responses. Tests: extend `test_prompt_service.py` (slot isolation is the key addition), `test_prompts_api.py`.
Frontend: extend `PromptEditor.tsx` with a conditional layer `<select>` (extract `LayerVariantPicker.tsx` if it pushes the file over 200), extend `PromptsPanel.tsx` to group by task + label scope + Add-variant action (extract a `PromptTaskGroup.tsx` if needed), extend `frontend/src/api/prompts.ts` + `frontend/src/types/prompt.ts`. Tests: extend `PromptEditor.test.tsx`, `PromptsPanel.test.tsx`.

## Acceptance criteria
- A user can add a layer-specific variant of any task's prompt from Settings; it coexists with the global prompt (global is NOT disabled).
- Generating at that layer uses the layer-specific prompt; generating at other layers continues to use the global prompt; the no-layer path is unchanged.
- The Prompts panel makes it unambiguous which prompt is Global and which is layer-specific.
- Old `call_logs` rows still reference valid unchanged versions (immutability holds; slots only add rows).
- Every touched frontend file strictly under 200 lines.
- `pnpm test` + `pnpm typecheck` + `pnpm build` + backend `pytest` all green and reported. Handoff in `docs/exchange/slice-19.md` with acceptance-to-test mapping.

## Constraints
- Schema-free; no migration. **Per-slot enabling is the critical invariant** — creating or promoting a layer variant MUST NOT disable the global prompt or any other slot (test this explicitly). `get_active` unchanged. `discipline_scope` stays NULL for all authored prompts this slice. Variable-contract validation unchanged (per task, layer-independent). `str.format` only. Reject `layer_id == Need`. One branch, one PR, no self-merge.