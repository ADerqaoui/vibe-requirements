# Slice 10 — Inspector (single-model review, lifecycle decisions, NeedList split)

Branch: `slice-10` (from `main`). Scope: run an **inspector pass** over an accepted Spec via a manually-selected local model, persist the **findings**, let the User accept or reject the Spec (lifecycle status transitions), and surface the spec's status visually. **First schema migration since 0001**. Pair with the long-deferred NeedList split (F4 from slices 06 / 09). Single-model inspection — multi-pass / multi-model voting is a later slice.

## In scope
1. **Schema migration `0002_add_spec_inspections`** — new table `spec_inspections`:
   - `id` INTEGER PRIMARY KEY, `spec_id` INTEGER NOT NULL REFERENCES `specs(id)` ON DELETE CASCADE, `model_id` INTEGER NOT NULL REFERENCES `models(id)`, `findings` TEXT NOT NULL (JSON), `summary` TEXT NULL, `passes` INTEGER NOT NULL DEFAULT 1 (room for future multi-pass), `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP. Index on `spec_id`. STRICT table.
2. **Inspector prompt** — `app/inspector/prompts.py`: `make_inspect_prompt(spec_statement) -> str`. Asks the model to evaluate the spec on five criteria (Clarity, Measurability, Testability, Atomicity, Ambiguity-free) and output one line per criterion: `- <Criterion>: PASS | FAIL — <short note>`. No commentary outside the lines.
3. **Findings parser** — `app/inspector/parser.py`: `parse_findings(text) -> dict`. Returns `{"criteria":[{"name","verdict","note"},...], "summary":<remaining text or null>}`. Permissive: matches lines case-insensitively, normalizes verdicts to `PASS`/`FAIL`/`UNCLEAR`, extracts trailing note text. Zero criteria parsed → clear error.
4. **Inspector service** — `app/services/inspector_service.py`: builds prompt, calls the slice-05 gateway service (logs `call_logs`, freezes cost), parses findings, **persists** a `spec_inspections` row, returns it. 409 if model missing/disabled; 502 if gateway fails (no row written); 422 if parser empty.
5. **Decision service + API** — `POST /api/specs/{spec_id}/decision` `{decision: 'accepted'|'rejected'}` → updates `specs.status`, bumps `updated_at`. 404 missing Spec; 422 invalid decision (must be in {accepted, rejected}; 'pending' is not settable here).
6. **Inspection API** — `POST /api/specs/{spec_id}/inspect` `{model_id}` → returns the persisted `SpecInspection` (with `id`, `findings`, `summary`, `created_at`, `model_id`). `GET /api/specs/{spec_id}/inspections` → list past inspections newest-first. 404 missing Spec.
7. **NeedList split (F4 finally)** — extract `NeedRow.tsx` from `NeedList.tsx` (the per-Need row: title, edit/delete, selection state). NeedList becomes < 200 lines and owns only list-level concerns (create, list, select-Need handler).
8. **Frontend Inspector UI** — on each Spec row in the recursive SpecList: an **Inspect** button next to the existing Classify button; an inline findings panel beneath the Spec when present (criteria with PASS/FAIL chips + note); **Accept** and **Reject** buttons that call the decision endpoint and update the spec's visual status badge (pending = neutral, accepted = green check, rejected = red strike-through). Model picker reuses the GenerationPanel's pattern.
9. **Tests** (deterministic, no live network):
   - Migration round-trip (upgrade → downgrade → upgrade clean).
   - Parser: all-PASS, mixed PASS/FAIL, missing-criterion (defaults UNCLEAR), unparseable → clear error, header/commentary skipped.
   - Inspector service: fake gateway returning a known findings text → persists row with correct `findings` JSON + `summary`; gateway failure → no row written + 502 surfaces; missing/disabled model → 409 before any call.
   - Decision API: 200 transitions `pending → accepted` and `pending → rejected`; 422 on invalid value; idempotent for same status; 404 missing Spec.
   - Inspection API: 200 with fake gateway, list returns newest-first; 404 missing Spec.
   - Frontend: Inspect button calls API (mocked) and renders findings; Accept/Reject buttons hit the decision endpoint and update the badge visually; NeedRow renders identically to the pre-split DOM (regression-safe).

## Out of scope (build NO behavior)
Multi-pass / multi-model voting on inspection (single-model only), auto-inspect after classify or generation, inspector findings in Markdown export (separate slice), re-inspection diff/comparison, blacklist of rejected statements, Router ON / auto model selection, prompt registry, cloud adapters, cost-ceiling enforcement (calls still log cost via the gateway service).

## API shapes
- `InspectRequest`: `{ model_id: int }`.
- `SpecInspection`: `{ id, spec_id, model_id, findings: { criteria: [{name, verdict, note}], summary?: str }, passes, created_at }`.
- `DecisionRequest`: `{ decision: 'accepted' | 'rejected' }`.
- `SpecOut` extended with optional `latest_inspection_id: int | None` (cheap join, no schema column needed — computed in the service).

## Suggested file layout (one entity/function per file, ≤200 lines)
Backend: `backend/alembic/versions/0002_add_spec_inspections.py`, `app/models/spec_inspection.py`, `app/inspector/prompts.py`, `app/inspector/parser.py`, `app/services/inspector_service.py`, `app/services/decision_service.py`, `app/schemas/inspection.py`, `app/schemas/decision.py`, `app/api/inspections.py`, `app/api/decisions.py` (register routers in `main.py`). Tests: `test_migration_0002.py`, `test_inspector_parser.py`, `test_inspector_service.py`, `test_inspections_api.py`, `test_decisions_api.py`.
Frontend: `src/api/inspections.ts`, `src/api/decisions.ts`, `src/types/inspection.ts`, `src/components/NeedRow.tsx` (extracted), thinned-down `src/components/NeedList.tsx`, extend `SpecList.tsx`/`SpecNode.tsx` with Inspect + Accept/Reject + findings panel + status badge, component tests.

## Acceptance criteria
- Clicking Inspect on a pending Spec with an enabled local model selected runs an inspection; a `spec_inspections` row is persisted; findings render as PASS/FAIL chips per criterion with notes.
- Accept transitions the Spec to `status='accepted'`; Reject transitions to `status='rejected'`; status is visible as a badge in the tree.
- `POST /api/specs/{id}/inspect`: 200 with persisted row; 404 missing Spec; 409 missing/disabled model; 422 parser-empty; 502 gateway failure (no row written).
- `POST /api/specs/{id}/decision`: 200 on valid transition; 422 invalid value; 404 missing Spec.
- `GET /api/specs/{id}/inspections` returns newest-first list scoped to that Spec.
- Migration 0002 round-trips cleanly (upgrade → downgrade → upgrade).
- `NeedList.tsx` is under 200 lines after the split; the rendered DOM for an existing Need row matches the pre-split rendering (regression-safe).
- `pytest` + `pnpm test` pass. Handoff in `docs/exchange/slice-10.md` with an acceptance-to-test mapping.

## Constraints
- Single-model inspection only — multi-pass / multi-model voting is a later slice. Keep the gateway dependency-injectable so tests use fakes, not live models. The new table must use STRICT mode and cascade-delete with the parent Spec. Reuse `/api/needs/{id}/spec-tree` (slice-09's design baseline) for any tree-related UI changes — do NOT introduce a competing tree-state pattern. One branch, one PR, no self-merge.
