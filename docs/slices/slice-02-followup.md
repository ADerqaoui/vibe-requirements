# Slice 02 — Follow-up (post-review tightening)

Continue on branch `slice-02`. Scope: test coverage + two small code changes from review.
**No new features, no schema changes, no new endpoints.**

## Tasks

### T1 — Test: exact layer-parent rules
In `backend/tests/test_seed.py`, after seeding, query `layer_parents` joined to `layers` by
name and assert the set of `(child_name, parent_name)` pairs equals the pairs in `LAYER_PARENTS`.
Counting rows is not enough.

### T2 — Test: blacklist parent CHECK invariant
On `blacklist_entries` (migrated session):
- both `parent_need_id` and `parent_spec_id` NULL → expect failure.
- both set → expect failure.
- exactly one set → succeeds (create a project + need inline for a valid parent).

### T3 — Test: frontend interactions
In `frontend/src/components/ProjectList.test.tsx` (Testing Library, mock fetch):
- create: name + submit calls POST /api/projects; new project appears and becomes selected.
- rename: calls PATCH; displayed name updates.
- delete: calls DELETE; item removed.
- highlight: clicking a project applies the selected/highlight class.

### T4 — Test: Projects API failure paths
In `backend/tests/test_projects.py`:
- two projects A, B; rename B to A's name → 409.
- rename a non-existent id → 404.
- delete a non-existent id → 404.

### T5 — Code: Alembic fail-fast on sqlite-vec
In `backend/alembic/env.py`, if sqlite-vec cannot load, do NOT silently continue — raise with
a clear message (migration 0001 requires the vec0 module). Leave the app's warn-and-continue
in `db.py` as is.

### T6 — Code: project name normalization
- In `backend/app/schemas/project.py`, field validator on `ProjectCreate.name` and
  `ProjectRename.name`: strip whitespace; reject empty-after-strip (422).
- Tests: `"  Alpha  "` then `"Alpha"` → second 409; `"   "` → 422.

## Acceptance
- `pytest` and `pnpm test` pass, including all new tests.
- `alembic env.py` raises a clear error when sqlite-vec is unavailable.
- Update the handoff in `docs/exchange/slice-02.md` under "## Codex — handoff & notes"
  (entry prefixed `[Codex — YYYY-MM-DD]`): the added tests + the two code changes; deviations honest.

## Constraints
- No schema changes, no new endpoints, nothing beyond the tasks above.
- Do not edit constitution docs. Do not read `.env`.
