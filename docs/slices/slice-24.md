# Slice 24 — Inspector findings in the Markdown export

Branch: `slice-24` (from `main`). Scope: include each spec's latest inspection (summary + per-criterion verdicts) in the Markdown export, so the deliverable is a real review artifact instead of a bare requirements list. The inspector has produced findings since slice 10 but they have never reached the export. **Schema-free** — reads the existing `spec_inspections` rows via the `latest_inspection_id` the spec-tree already exposes; runs no new inspections.

## In scope

1. **Render the latest inspection under each spec** in the Markdown export. For a spec that has a `latest_inspection_id`, append an inspection block after the requirement, containing:
   - the inspection **summary** (if present),
   - the **criteria** as a compact list — `<name>: <verdict>` with the `note` appended for non-PASS verdicts (FAIL / UNCLEAR), e.g.:
     ```
     - Verifiability: FAIL — no measurable acceptance threshold given
     - Atomicity: UNCLEAR — combines two requirements
     - Clarity: PASS
     ```
   - the inspecting **model name** + inspection **date** as a one-line header (e.g. `Inspection (qwen2.5:7b, 2026-06-05):`).
   - Use the **latest** inspection only (the spec-tree's `latest_inspection_id`; ordering already defined as created_at DESC, id DESC). A spec with multiple inspections shows just the most recent.

2. **Defensive rendering** — a spec with **no** inspection renders no inspection block (just the requirement, as today). An inspection whose stored `findings` JSON is empty/criteria-less renders the summary only (or nothing if both are empty). Malformed/unparseable stored findings must not crash the export — skip the block and continue. (Do NOT add findings JSON schema versioning here — it stays deferred; just read the current shape `{ criteria: [{name, verdict, note}], summary }` defensively.)

3. **Toggle** — the export accepts a query param `include_inspections` (boolean, **default true**). `false` produces the prior requirements-only export (so a clean requirements document is still available). This keeps both artifacts — review doc (default) and requirements-only — from one endpoint.

4. **Frontend** (only if an export trigger/UI exists) — add an **"Include inspection findings"** checkbox (default checked) to the export control, passing `include_inspections` through. If the export is a plain download link with no options UI, the default-true param is sufficient and no UI change is required; state which in the handoff. Keep any touched file strictly under 200 lines.

5. **Tests** (deterministic):
   - export of a spec with one inspection includes its summary + each criterion with verdict; FAIL/UNCLEAR include their notes; PASS criteria render without forcing a note.
   - a spec with **multiple** inspections renders only the latest (by the established ordering).
   - a spec with **no** inspection renders no inspection block.
   - an inspection with empty/criteria-less findings renders gracefully (summary-only or nothing), no crash.
   - malformed stored `findings` JSON → block skipped, export still succeeds.
   - `include_inspections=false` → output identical to the prior requirements-only export (regression-lock the old format).
   - `include_inspections=true` (default) → inspection blocks present.
   - frontend (if applicable): the checkbox toggles the param; default checked.

## Out of scope (build NO behavior)
- Findings JSON schema versioning (still deferred; render the current shape defensively).
- Showing inspection history (more than the latest) in the export.
- Re-running or triggering inspections during export.
- Findings in non-Markdown formats (no other export format exists yet — CSV/DOCX/ReqIF are later).
- Changing inspection storage, the inspector, or the findings parser.
- Per-criterion filtering/sorting controls.

## API shapes
- The existing Markdown export endpoint gains a `include_inspections` query param (boolean, default true). No new endpoints. No schema changes.

## Suggested file layout (one entity per file, ≤200 lines)
Backend: extend `export_markdown.py` (fetch each spec's latest inspection via `latest_inspection_id`; render the inspection block; honor `include_inspections`); a small helper to format one inspection's findings into Markdown lines; thread the query param through the export route. Tests: extend `test_export_markdown.py` + `test_export_api.py`.
Frontend (if an export UI exists): add the checkbox to the export control + pass the param; otherwise no change. Tests: export-control test addition if applicable.

## Acceptance criteria
- The default Markdown export now shows, under each inspected requirement, the latest inspection's summary and per-criterion verdicts (with notes on FAIL/UNCLEAR).
- Uninspected specs and specs with empty/malformed findings render cleanly (no crash, no empty noise).
- `include_inspections=false` reproduces the prior requirements-only export exactly.
- `pnpm test` + `pnpm typecheck` + `pnpm build` + backend `pytest` all green and reported. Handoff in `docs/exchange/slice-24.md` with acceptance-to-test mapping (and a note on whether a frontend export-UI checkbox was added or the default-param sufficed).

## Constraints
- Schema-free; no migration; read existing `spec_inspections` only, no new inspections run. Latest inspection only. Defensive against missing/empty/malformed findings — the export must never crash on bad stored data. `include_inspections=false` must be byte-for-byte the old export (regression-tested). Do not modify the inspector, its parser, or findings storage. One branch, one PR, no self-merge. All four checks green per docs/MERGE-CHECKLIST.md.