# Slice 09 — Spec → child-Spec generation (extend the V-model hierarchy)

Branch: `slice-09` (from `main`). Scope: extend slice-06's generation path so a **Spec** can also be a parent — generate child Specs from a selected Spec, Accept/Reject the same way, persist as deeper Specs in the existing `specs` table via `parent_spec_id`. **Schema-free**. Same gateway, same parser, same prompt template (parameterized on parent statement only).

## In scope
1. **Spec-level generate API** — `POST /api/specs/{spec_id}/generate` `{model_id, count: 1..10}` → `{candidates: [{index, statement}]}`. Mirrors slice-06's `POST /api/needs/{need_id}/generate`. 404 missing Spec; 409 missing/disabled model; 422 invalid count or parser-empty; 502 gateway failure.
2. **Child-Spec persistence** — `POST /api/specs/{spec_id}/specs` `{statement}` → 201 SpecOut creating a child Spec via `parent_spec_id`; status starts as `'pending'` (same lifecycle as slice 06). 404 missing parent; 422 blank statement. `GET /api/specs/{spec_id}/specs` lists the parent's **direct children** only.
3. **Generation service refactor (minimal)** — extract a single `generate_for_parent(parent_kind, parent_id, model_id, count)` that serves both `kind='need'` and `kind='spec'`. The slice-06 endpoint becomes a thin wrapper; its tests must continue to pass byte-identical (no prompt or parser changes).
4. **Frontend** — when a Spec is selected (clicked) in the tree, surface the existing GenerationPanel pointed at `/api/specs/{spec_id}/generate`. Accept hits `/api/specs/{spec_id}/specs`; children appear as nested Specs under the parent. SpecList becomes recursive (or extract a `SpecNode.tsx` if SpecList crosses 200 lines). Stale-candidate clearing must apply to **every parent change** (Need-or-Spec) — same regression guard as slice-06 F1.
5. **Tests** (deterministic, no live network):
   - API: `POST /api/specs/{id}/generate` 200/404/409/422/502 with fake gateway.
   - API: `POST /api/specs/{id}/specs` 201 with parent_spec_id set; 404 missing parent; 422 blank; `GET` returns only the parent's direct children (not grandchildren).
   - Service: parametrize the generation-service test over `kind='need'` and `kind='spec'`.
   - Frontend: nested SpecList renders children; selecting a child Spec shows the GenerationPanel against the spec endpoint; Accept persists; stale candidates clear on parent change Need→Spec, Spec→Spec, and Spec→Need.
   - Regression: slice-06 Need-side tests still pass unchanged.

## Out of scope (build NO behavior)
Explicit V-model layer selection on child Specs (same default applies per the slice-06 ruling), per-model vote persistence, inspector, blacklist, auto-classify-on-Accept, prompt-registry overrides, cloud adapters, Router ON, recursive-depth cap.

## API shapes
- `GenerationRequest`, `GenerationResult`, `SpecCreate`, `SpecOut` — reused from slice 06.
- `GET /api/specs/{spec_id}/specs` → `SpecOut[]` filtered by `parent_spec_id`.

## Suggested file layout (one entity/function per file, ≤200 lines)
Backend: extend `app/services/generation_service.py` with `generate_for_parent(kind, id, model_id, count)`; extend `app/services/spec_service.py` with `create_spec_for_parent_spec` + `list_children_of_spec`; extend `app/api/specs.py` (or add `app/api/spec_children.py`) for the two new endpoints + `register_router`. Tests: parametrize `test_generation_service.py` over parent kind, add `test_spec_children_api.py`, extend `test_specs_api.py`.
Frontend: extend `src/api/generation.ts` and `src/api/specs.ts` with spec-parent variants; refactor `src/components/SpecList.tsx` to be recursive (or extract `SpecNode.tsx`). Tests: nested rendering, spec-parent generate/accept, cross-parent stale-clearing.

## Acceptance criteria
- Selecting a Spec → Generate yields N parsed candidate child statements; Accept creates a child Spec with `parent_spec_id` set and `status='pending'`; the child appears nested under the parent.
- `POST /api/specs/{id}/generate` and `POST /api/specs/{id}/specs` cover the same status codes as the Need-side endpoints.
- Need → Spec generation (slice 06) and its tests are unchanged.
- Classification (slice 07) and Markdown export (slice 08) continue to work for deeper Specs without modification.
- Stale candidates are cleared whenever the selected parent changes (Need ↔ Spec at any depth).
- `pytest` + `pnpm test` pass. Handoff in `docs/exchange/slice-09.md` with an acceptance-to-test mapping.

## Constraints
- No schema changes. Generation-service refactor preserves slice-06 behavior byte-for-byte (same prompt, same parser). Frontend recursion: visual depth via indentation; no hard depth cap. Keep the gateway dependency-injectable. One branch, one PR, no self-merge.
