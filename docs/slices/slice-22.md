# Slice 22 — Manual spec editing + stable requirement IDs

Branch: `slice-22` (from `main`). Scope: let a user **edit a spec's text** after generation (flipping it to a manual-source requirement), and give every spec a **stable, citable requirement ID** (`REQ-<LAYER>-<NNNN>`) surfaced in the tree and the Markdown export. This closes the two biggest "demo → real tool" gaps: today you can only accept AI text verbatim or reject it, and requirements have no referenceable identifiers. **One small migration** (a single nullable column); backfill runs in the seed runner, not the migration.

## In scope

1. **Migration `0003_add_spec_req_id`** — add a single nullable column to `specs`: `req_id TEXT` (no default, nullable). That is the entire migration — no data step inside it (keeps it the lowest-risk kind of migration). Do not touch any other table or column.

2. **Requirement ID format + assignment**:
   - Format: `REQ-<LAYER_ABBREV>-<NNNN>` — e.g. `REQ-SYS-0001`, `REQ-SWR-0012`. `NNNN` is zero-padded to 4 digits, **sequential per (project, layer)**.
   - `LAYER_ABBREV` comes from a code-side mapping (a constants module), e.g. System Requirement→`SYS`, System Architecture→`SYSA`, SW Requirement→`SWR`, SW Architecture→`SWA`, SW Component/Unit→`SWC`, Electronic Requirement→`ELR`, Electronic Architecture→`ELA`, Electronic Component→`ELC`, Mechanical Requirement→`MER`, Mechanical Architecture→`MEA`, Mechanical Component→`MEC`. Codex may finalize the exact abbreviations but they must be stable and unique.
   - Assign `req_id` **at spec row creation** in both `create_spec_for_need` and `create_spec_for_parent_spec`. The next sequence number for a `(project, layer)` is computed from existing rows: parse the trailing `NNNN` of existing `req_id`s in that project+layer, take max+1 (start at 1). Derive `project_id` via the spec's `need_id → need.project_id`.
   - `req_id` is **frozen once assigned** — it never changes on edit, re-classify, status change, or anything else. It is a stable citable identifier even though its abbreviation was seeded from the layer. (A spec's layer doesn't change in this slice anyway.)
   - Every spec row gets a `req_id`, regardless of status (a rejected requirement keeps its ID, which is correct for audit).

3. **Backfill existing specs (in the seed runner, not the migration)**: extend `python -m app.seed.run` to assign `req_id` to any spec where `req_id IS NULL`, deterministically ordered by `(project_id, layer_id, id ASC)` so existing specs get sequential IDs in creation order. **Idempotent** — never reassigns a spec that already has a `req_id`. This is where the user's existing `reqdash.db` specs get their IDs (and it self-heals on the next `run-backend.sh` start, consistent with how seeding already works).

4. **Edit endpoint** — `PATCH /api/specs/{spec_id}` with body `{ text }`:
   - Updates `text`, sets `source = "manual"`, bumps `updated_at`. Returns the updated `SpecOut`.
   - `req_id`, `layer_id`, `status`, `complexity` are unchanged by this endpoint (text-only edit this slice).
   - Empty/whitespace-only `text` → 422. Unknown `spec_id` → 404.
   - Editing is allowed regardless of status (pending/accepted/rejected).
   - In-place edit (mutable) — full edit/revision history (`spec_revisions`) remains a separate deferred slice; note that in the handoff.

5. **Expose `req_id` + `source`** in `SpecOut` and the spec-tree node shape, so the frontend can show the ID and whether a spec is AI- or manually-sourced.

6. **Export** — the Markdown export prefixes each requirement with its `req_id` (e.g. `**REQ-SYS-0001** — <text>`), so the deliverable carries citable IDs. Keep the rest of the export format as-is.

7. **Frontend**:
   - Each spec node displays its `req_id` (as a label/prefix) and a small **source badge** (AI / Manual).
   - An **Edit** affordance on a spec node opens an inline textarea prefilled with the current text; Save → `PATCH /api/specs/{id}` → refreshes the tree; the source badge flips to Manual. Cancel discards.
   - Keep every touched file strictly under 200 lines. **Heads-up:** `NeedList.tsx` is at 196 and `useGenerationActions.ts` at 199 — if wiring edit/req_id pushes either over, extract (e.g. a `SpecEditor.tsx` and/or moving spec-node rendering into its own component). Do not exceed 200.

8. **Tests** (deterministic):
   - **migration**: `0003` adds the `req_id` column; existing schema otherwise unchanged.
   - **req_id assignment**: `create_spec_for_need` + `create_spec_for_parent_spec` assign `REQ-<ABBREV>-<NNNN>`; format correct; per-(project, layer) sequence increments (two specs at the same project+layer → `0001`, `0002`); two different layers in the same project get independent sequences; `req_id` is unchanged after a subsequent `PATCH` edit (stable).
   - **backfill**: a spec row with `req_id IS NULL` gets assigned by the seed runner in `(project, layer, id)` order; running the seed twice does NOT reassign (idempotent).
   - **edit**: `PATCH` updates text + sets `source="manual"` + bumps `updated_at`; empty text → 422; unknown spec → 404; `req_id`/`layer_id`/`status` unchanged.
   - **serialization**: `SpecOut` + tree include `req_id` + `source`.
   - **export**: rendered Markdown includes each spec's `req_id`.
   - **frontend**: edit flow (prefilled → save → tree refresh → source badge flips to Manual); `req_id` + source badge render on nodes; empty-text save blocked/handled.

## Out of scope (build NO behavior)
- Manual spec creation from scratch (authoring a brand-new requirement by hand) — a clean separate fast-follow.
- Edit/revision history (`spec_revisions`) — in-place edit only this slice; the ISO-26262 audit-history slice is still deferred.
- Editing a spec's layer, status, or complexity through the edit endpoint (text only).
- Configurable ID format, ID renumbering/reuse, project-wide (non-layer) numbering.
- Prompt preview/test-run (separate).

## API shapes
- Migration `0003_add_spec_req_id` (nullable `req_id TEXT`).
- `PATCH /api/specs/{spec_id}` body `{ text }` → 200 `SpecOut` / 422 empty / 404 unknown (new).
- `SpecOut` + spec-tree node gain `req_id` + `source`.
- Markdown export includes `req_id` per spec.
- No other schema changes.

## Suggested file layout (one entity per file, ≤200 lines)
Backend: `backend/alembic/versions/0003_add_spec_req_id.py` (column only); a small `req_id` helper module (abbrev mapping + next-sequence computation + format); assign in `spec_service.create_spec_for_need`/`create_spec_for_parent_spec`; `PATCH` handler in `app/api/specs.py` + an `update_spec_text` service fn; extend the seed runner with the idempotent backfill; extend `SpecOut`/tree schema; extend the export renderer. Tests: `test_migration_0003.py`, `test_req_id.py`, extend `test_specs_api.py`, `test_seed.py`, `test_export_markdown.py`.
Frontend: a `SpecEditor.tsx` (inline edit) + req_id/source badges on the spec node (extract a spec-node component if needed to stay under 200), extend `api` + types. Tests: `SpecEditor.test.tsx` + spec-tree/node additions.

## Acceptance criteria
- Every spec — newly generated and pre-existing (after the seed backfill) — has a stable `REQ-<LAYER>-<NNNN>` ID, visible in the tree and the export.
- A user can edit a spec's text in-place; the spec's source flips to Manual; the `req_id` does not change.
- IDs are sequential per (project, layer) and never reassigned.
- The migration is a clean nullable-column add; the backfill is idempotent and runs via the seed.
- Every touched frontend file strictly under 200 lines.
- `pnpm test` + `pnpm typecheck` + `pnpm build` + backend `pytest` all green and reported. Handoff in `docs/exchange/slice-22.md` with acceptance-to-test mapping.

## Constraints
- Exactly one migration, and only the nullable `req_id` column — no data step in the migration (backfill belongs in the seed runner). `req_id` is immutable once assigned. Edit endpoint changes `text` + `source` only. Sequence is per (project, layer), computed from existing rows (single-user, no counter table needed). `str.format`/prompt path untouched. One branch, one PR, no self-merge. All four checks green per docs/MERGE-CHECKLIST.md.