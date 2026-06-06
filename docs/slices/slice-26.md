# Slice 26 — Spec revision history (audit trail)

Branch: `slice-26` (from `main`). Scope: record an immutable, per-spec history of every meaningful change — creation, text edit, status change — so an edited requirement has a defensible trail and the export/UI can show how a requirement evolved. This is the "controlled requirements" substrate (ISO-flavored) and the last V1 feature. **One small migration** (a new table, slice-22's clean-table-create pattern); backfill an initial revision for existing specs in the seed runner.

## In scope

1. **Migration `0004_add_spec_revisions`** — create one table, nothing else:
   ```
   CREATE TABLE spec_revisions (
       id              INTEGER PRIMARY KEY,
       spec_id         INTEGER NOT NULL REFERENCES specs(id) ON DELETE CASCADE,
       revision_number INTEGER NOT NULL,
       text            TEXT NOT NULL,
       status          TEXT NOT NULL,
       source          TEXT NOT NULL,
       change_type     TEXT NOT NULL,          -- created | text_edited | status_changed
       created_at      TEXT NOT NULL DEFAULT (datetime('now'))
   ) STRICT
   ```
   Index on `spec_id`; `UNIQUE(spec_id, revision_number)`. `created_at` uses the table default `datetime('now')` (consistent with `spec_inspections`) — do not set it from Python.

2. **Revision recording** — a single helper `record_spec_revision(db, spec, change_type)` that snapshots the spec's **current** `text`, `status`, `source`, assigns `revision_number = (max for that spec) + 1` (starts at 1), and inserts a row. It is called **within the same transaction as the mutation** (the revision and the change commit together; for `created`, flush so the spec has an id before recording). Hook it into exactly three places:
   - `create_spec_for_need` + `create_spec_for_parent_spec` → `change_type="created"` (this also covers manual creation from slice 23, which routes through these).
   - `update_spec_text` (slice 22) → `change_type="text_edited"`.
   - `decide_spec` (slice 6 — accept/reject) → `change_type="status_changed"`.

3. **Backfill (seed runner, not the migration)** — extend `python -m app.seed.run`: for any spec with **zero** revisions, insert an initial `change_type="created"` revision (number 1) snapshotting its **current** text/status/source. Idempotent — a spec that already has revisions is skipped, and re-running never duplicates. (For pre-existing specs the snapshot is current state, since the original isn't recoverable — that's the accepted baseline; note it in the handoff.)

4. **History endpoint** — `GET /api/specs/{spec_id}/revisions` → `list[SpecRevisionOut]` (`revision_number, text, status, source, change_type, created_at`), ordered by `revision_number` ascending (chronological). 404 if the spec is unknown.

5. **Frontend** — a **"History"** affordance on each spec node → a `SpecHistoryPanel` (modal or expandable region) showing the revision timeline: per revision, the `change_type` (as a readable label — Created / Text edited / Status changed), the timestamp, and the `text` + `status` snapshot at that revision. **Read-only** — no diff, no revert this slice. Keep every touched file strictly under 200 lines — extract `SpecHistoryPanel.tsx` rather than enlarging the spec node.

6. **Tests** (deterministic):
   - **migration**: `0004` creates `spec_revisions` with the `UNIQUE(spec_id, revision_number)` constraint.
   - **created**: creating a spec (AI path) writes revision 1, `change_type="created"`, snapshot matching the new spec's text/status/source.
   - **text edit**: `update_spec_text` writes revision 2, `change_type="text_edited"`, with the new text; revision 1 is unchanged (immutability).
   - **status change**: `decide_spec` (accept and reject) writes a `status_changed` revision capturing the new status.
   - **manual create**: a manual spec (source="manual", status="accepted") gets a `created` revision capturing `source="manual"` + `status="accepted"` — i.e. its history starts created+accepted, whereas an AI spec's history is created+pending then status_changed+accepted (this is the authored-accept vs reviewed-accept distinction, now visible from history with no extra fields).
   - **numbering**: `revision_number` is per-spec sequential; two specs have independent sequences; the unique constraint holds.
   - **backfill**: a spec with no revisions gets a `created` revision 1 via the seed; running the seed twice does not duplicate (idempotent).
   - **API**: `GET /api/specs/{id}/revisions` returns the history in ascending order; unknown spec → 404.
   - **frontend**: the history panel lists revisions with their change-type labels, timestamps, and text/status snapshots; opens read-only.

## Out of scope (build NO behavior)
- Diff view between revisions (snapshots only; diff is a future nicety).
- Reverting/restoring a spec to a past revision (read-only history this slice).
- Recording complexity/classification changes as revisions (machine-derived + re-runnable; complexity is deliberately not in the snapshot — deferred).
- Multi-user "who" actor tracking (single-user; the `source` snapshot is the closest proxy).
- A separate authored-vs-reviewed status field (the history makes the distinction visible without it).
- Revisions for Needs (specs only).

## API shapes
- `GET /api/specs/{spec_id}/revisions` → `list[SpecRevisionOut]` (ascending) / 404 (new).
- Migration `0004_add_spec_revisions` (one table).
- No changes to existing endpoint shapes.

## Suggested file layout (one entity per file, ≤200 lines)
Backend: `backend/alembic/versions/0004_add_spec_revisions.py` (table only); a `SpecRevision` model; `record_spec_revision(...)` in a `spec_revision_service.py`; call it from `spec_service` (create + update_spec_text) and `decision_service`; `SpecRevisionOut` schema; the revisions route; backfill in the seed runner. Tests: `test_migration_0004.py`, `test_spec_revisions.py`, extend `test_specs_api.py`, `test_seed.py`.
Frontend: `SpecHistoryPanel.tsx` + a History trigger on the spec node, `api`/types additions. Tests: `SpecHistoryPanel.test.tsx`.

## Acceptance criteria
- Every spec accrues an immutable revision trail: a `created` revision, plus a new revision on each text edit and status change, each snapshotting text/status/source with a change type and timestamp.
- Existing specs are backfilled with a baseline `created` revision (idempotently) via the seed.
- The history is viewable per spec (API + read-only UI), in chronological order.
- A manual spec's history is distinguishable from an AI-then-accepted spec's history with no new fields.
- The migration is a clean single-table create; the backfill is idempotent and runs via the seed.
- Every touched frontend file strictly under 200 lines.
- `pnpm test` + `pnpm typecheck` + `pnpm build` + backend `pytest` all green and reported. Handoff in `docs/exchange/slice-26.md` with acceptance-to-test mapping.

## Constraints
- Exactly one migration, only the `spec_revisions` table (no data step in the migration — backfill belongs in the seed runner). Revisions are append-only/immutable — never updated or deleted except via the spec's ON DELETE CASCADE. `record_spec_revision` runs in the same transaction as the mutation it records (no orphan/missing revisions). Snapshot = text/status/source only (no complexity this slice). `created_at` via the table default. One branch, one PR, no self-merge. All four checks green per docs/MERGE-CHECKLIST.md.