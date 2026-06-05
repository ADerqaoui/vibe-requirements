# Slice 23 — Manual spec creation (author a requirement by hand)

Branch: `slice-23` (from `main`). Scope: let a user author a brand-new spec by hand — under a Need (top-level) or under a parent Spec (child at the next layer) — at a chosen V-model layer, instead of only accepting AI-generated candidates. This completes the authoring story alongside slice 22's editing: you can now write a requirement the AI never generated. **Schema-free** — reuses the `specs` table, slice-22's `req_id` assignment + `source` field, and slice-18's `layer_parents` validation.

## In scope

1. **Service** — parametrize the existing create functions rather than duplicating them:
   - `create_spec_for_need(db, need_id, statement, target_layer_id=None, source="ai", status="pending")` — add `source` + `status` params (defaults preserve today's AI-accept behavior exactly).
   - `create_spec_for_parent_spec(db, spec_id, statement, target_layer_id=None, source="ai", status="pending")` — same.
   - Manual creation calls these with `source="manual"`, `status="accepted"`. `req_id` is still assigned via `next_req_id(...)` (unchanged), layer is still resolved/validated via `resolve_target_layer_for_need` / `resolve_target_layer_for_spec` (slice 18 — disallowed layer → the existing 422 `layer_not_allowed_for_parent`).
   - **Status decision**: a hand-authored requirement is `status="accepted"` — it's deliberate, not a candidate awaiting review. (It can still be edited via slice-22 PATCH and re-decided via the existing decision endpoint.)

2. **Routes** (`app/api/specs.py`):
   - `POST /api/needs/{need_id}/specs/manual` — body `{ text, target_layer_id }` → creates a manual top-level spec under the Need.
   - `POST /api/specs/{spec_id}/specs/manual` — body `{ text, target_layer_id }` → creates a manual child spec under the parent Spec.
   - Both: validate `target_layer_id` is an allowed child of the parent (422 on violation — reuse the slice-18 path); empty/whitespace `text` → 422; unknown need/parent → 404. Return the created `SpecOut` (201), carrying `req_id` + `source="manual"`.
   - These are distinct from the existing AI-accept routes (`POST /api/needs/{need_id}/specs` and `POST /api/specs/{spec_id}/specs`), which keep `source="ai"`, `status="pending"` behavior unchanged.

3. **Frontend**:
   - An **"Add requirement"** action under a Need and on each Spec node → opens a small form: a **layer `<select>`** (allowed children of that parent, via the existing `useAllowedChildLayers` hook — default = single allowed child or lowest `sort_order`) + a **text textarea**. Save → `POST .../manual` → refresh the spec tree; Cancel discards.
   - The new spec appears in the tree with its `req_id` and the **Manual** source badge (both already rendered since slice 22).
   - Blank text is blocked client-side (mirrors the SpecEditor from slice 22).
   - Keep every touched file strictly under 200 lines. **Heads-up:** `SpecNode.tsx` (198), `NeedList.tsx` (196), `useGenerationActions.ts` (199) are all near the limit — extract (e.g. a `ManualSpecForm.tsx`, and/or move spec-node rendering out) rather than exceed 200.

4. **Tests** (deterministic):
   - **service**: `create_spec_for_need` with `source="manual", status="accepted"` persists a manual accepted spec with a `req_id` at the resolved layer; defaults still produce `source="ai", status="pending"` (no regression to the AI path); disallowed `target_layer_id` → raises the layer-not-allowed error; empty text rejected.
   - **manual under parent spec**: layer must be an allowed child of the parent's layer; `req_id` assigned; `need_id` inherited from the parent.
   - **API**: `POST /api/needs/{need_id}/specs/manual` and `POST /api/specs/{spec_id}/specs/manual` → 201 with `source="manual"`, `status="accepted"`, a `req_id`, correct layer; 422 on empty text; 422 on disallowed layer; 404 on unknown need/parent.
   - **tree**: a manually-created spec appears in the spec-tree with `source="manual"` + its `req_id`.
   - **regression**: the existing AI-accept routes still create `source="ai"`, `status="pending"` specs.
   - **frontend**: Add-requirement form lists allowed child layers, defaults correctly, posts `{text, target_layer_id}`, refreshes the tree; blank text blocked; new node shows the Manual badge + req_id.

## Out of scope (build NO behavior)
- Editing a spec's layer after creation (slice 22 is text-only; layer is fixed at creation).
- Bulk creation / paste-many / import.
- Manual creation of Needs (Needs CRUD already exists from slice 3).
- Reordering specs within a layer.
- Revision history for manual specs (still the deferred `spec_revisions` slice).
- ASIL or any new attribute (V2/RAG).

## API shapes
- `POST /api/needs/{need_id}/specs/manual` `{ text, target_layer_id }` → 201 `SpecOut` / 422 / 404 (new).
- `POST /api/specs/{spec_id}/specs/manual` `{ text, target_layer_id }` → 201 `SpecOut` / 422 / 404 (new).
- `create_spec_for_need` / `create_spec_for_parent_spec` gain `source` + `status` params (defaults unchanged).
- No schema changes.

## Suggested file layout (one entity per file, ≤200 lines)
Backend: add `source`/`status` params to the two create fns in `spec_service.py`; manual route handlers + request schema in `app/api/specs.py` (+ a `ManualSpecCreate` schema). Tests: extend `test_specs_api.py`, `test_spec_service.py` (or the relevant spec-creation test).
Frontend: `ManualSpecForm.tsx` (layer select + textarea, reuses `useAllowedChildLayers`), an "Add requirement" trigger on the Need header and Spec nodes, `api`/types additions. Extract spec-node rendering into its own component if `SpecNode.tsx`/`NeedList.tsx` would cross 200. Tests: `ManualSpecForm.test.tsx` + tree/node additions.

## Acceptance criteria
- A user can add a hand-written requirement under a Need or any Spec, choosing from the allowed child layers; it persists as `source="manual"`, `status="accepted"`, with a real `req_id`, and appears in the tree + export like any other spec.
- A manual spec at a disallowed layer for its parent is rejected (422); empty text is rejected.
- The AI-accept flow is unchanged (regression-tested).
- Manual specs are first-class: they can be edited (slice 22), classified, inspected, generated-from, and exported — no special handling needed.
- Every touched frontend file strictly under 200 lines.
- `pnpm test` + `pnpm typecheck` + `pnpm build` + backend `pytest` all green and reported. Handoff in `docs/exchange/slice-23.md` with acceptance-to-test mapping.

## Constraints
- Schema-free; no migration. Reuse `next_req_id` + the slice-18 layer resolvers — do not reimplement layer validation or ID allocation. Parametrize the create fns with safe defaults so the AI path is byte-for-byte unchanged. Manual specs are `source="manual"`, `status="accepted"`. One branch, one PR, no self-merge. All four checks green per docs/MERGE-CHECKLIST.md.