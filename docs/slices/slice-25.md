# Slice 25 — Prompt preview / test-run

Branch: `slice-25` (from `main`). Scope: dry-run a prompt template — **including unsaved draft text** — against sample input, showing the rendered prompt, the model's actual output, and the cost, so a syntactically-valid-but-poor-quality prompt is caught *before* it's promoted or used. This is the safety net for the prompt-editing machinery built across slices 17/19/21. **Schema-free** — reuses `validate_template` (slice 17), `complete_model` + the cost ceiling (slices 15/20), and the router default (slice 20); persists no spec or inspection.

## In scope

1. **Preview endpoint** — `POST /api/prompts/preview`, body `{ task, template, variables: { <var>: <value>, ... }, model_id? }`:
   - **Validate** the template for the task via `validate_template(task, template)` → 422 `PromptTemplateInvalidError` on invalid; unknown task → 422. (Same validation as saving a version — so "preview passes" implies "would save cleanly," plus you see output.)
   - **Render** the template with the supplied `variables` (the existing `str.format` render path). A missing/empty required variable → 422 with a clear message (reuse the `PromptRenderError` / `PromptVariableMissingError` path).
   - **Run** the rendered prompt through `complete_model` with `task="preview"`. This means the cost ceiling is enforced exactly as in generation (`enforce_cost_ceiling` is already inside `complete_model`) → 402 with the existing `{error, spent_sek, ceiling_sek, currency}` body when a paid model is over budget; free/local models always run. `model_id` is **optional** — when omitted, fall back to the task's routed/default model (`select_model`, slice 20).
   - **Persist nothing structural**: NO spec, NO inspection created. The underlying `call_log` IS written (by `complete_model`) with `task="preview"` so the cost is honestly counted toward the monthly ceiling — a preview costs real money on a paid model and must count. (`call_logs.task` is free-text, no constraint — `"preview"` is fine and distinguishes these from real generation.)
   - **Returns** `{ rendered_prompt, output, model_id, model_name, cost_sek }`.

2. **Contracts endpoint** — `GET /api/prompts/contracts` → `{ "<task>": ["<var>", ...], ... }` sourced from `REQUIRED_VARIABLES_BY_TASK`, so the editor knows which variable input fields to render per task (rather than hard-coding them client-side). (Generation tasks → `parent_statement`, `count`; classify/inspect → `spec_statement`.)

3. **Frontend** — a **Test-run panel** inside the prompt editor:
   - One input field per required variable for the editor's task (from `GET /api/prompts/contracts`), each **prefilled with a short example** (e.g. a sample parent statement, count `3`), editable.
   - An optional **model picker** (default = the routed/default model).
   - A **"Run preview"** button → `POST /api/prompts/preview` with the **current draft template in the editor** (not the saved version) + the variable values + model.
   - Renders the result: the **rendered prompt**, the **model output**, and the **cost** of the run (cost transparency).
   - Surfaces a 422 invalid-template reason inline; reuses the existing cost-ceiling 402 handling (`useCostCeilingError`, slice 15) so an over-budget preview shows the same banner as generation.
   - Keep every touched file strictly under 200 lines — extract a `PromptPreviewPanel.tsx` rather than bloating the editor.

4. **Tests** (deterministic; mock the gateway, no live model calls):
   - **valid preview**: valid template + sample vars + model → returns `rendered_prompt` (vars substituted) + `output` (from mocked gateway) + `cost_sek`.
   - **invalid template** → 422 (e.g. missing required variable in the template, or unexpected variable).
   - **missing variable value** at render → 422 with a clear message.
   - **cost ceiling** exceeded with a paid model → 402 with the standard body (reuse slice-15 behavior).
   - **no persistence**: spec count and inspection count are unchanged after a preview run.
   - **cost counted**: a `call_log` row with `task="preview"` is written and its cost contributes to the monthly spend / cost-summary.
   - **model fallback**: `model_id` omitted → uses the routed/default model.
   - **contracts endpoint**: returns the correct required variables for each task.
   - **frontend**: the preview panel renders one field per required variable for the task, runs the preview against the current draft template, displays rendered prompt + output + cost; an invalid template shows its reason.

## Out of scope (build NO behavior)
- Turning a preview output into a real spec/inspection (dry-run only).
- Side-by-side A/B or diff of two prompts/outputs.
- Batch preview over multiple sample inputs.
- Saving/persisting preview history.
- Preview influencing active-prompt selection or the router.
- Any change to the inspector, classifier, generation persistence, or prompt storage.

## API shapes
- `POST /api/prompts/preview` `{ task, template, variables, model_id? }` → 200 `{ rendered_prompt, output, model_id, model_name, cost_sek }` / 422 invalid template or missing variable / 402 ceiling (new).
- `GET /api/prompts/contracts` → `{ task: [required vars] }` (new).
- No schema changes.

## Suggested file layout (one entity per file, ≤200 lines)
Backend: a `prompt_preview_service.py` (validate → render → run via `complete_model` with `task="preview"`, return the result; no persistence); preview + contracts routes + request/response schemas in the prompts API module; reuse `validate_template`, the render path, `complete_model`, `select_model`. Tests: `test_prompt_preview.py` (+ a cost-summary assertion in the existing cost test if convenient).
Frontend: `PromptPreviewPanel.tsx` (variable fields from contracts + model picker + run + result display), a `useContracts` fetch, `api`/types additions, wire into the prompt editor. Tests: `PromptPreviewPanel.test.tsx`.

## Acceptance criteria
- From the prompt editor, a user can enter sample variable values, run the **current draft** template against a model, and see the rendered prompt + the model's output + the run cost — without saving the prompt or creating any spec/inspection.
- An invalid template is rejected with its reason (same validation as saving); an over-budget paid run returns 402; the preview's cost is counted toward the monthly ceiling.
- With `model_id` omitted, the routed/default model is used.
- Every touched frontend file strictly under 200 lines.
- `pnpm test` + `pnpm typecheck` + `pnpm build` + backend `pytest` all green and reported. Handoff in `docs/exchange/slice-25.md` with acceptance-to-test mapping.

## Constraints
- Schema-free; no migration. Reuse `validate_template`, the existing render path, `complete_model` (with the cost-ceiling enforcement it already performs), and `select_model` — do not reimplement validation, rendering, cost, or routing. Preview runs use `task="preview"`; they write a `call_log` (cost honesty) but create NO spec or inspection. Works on unsaved draft template text — the preview must not require the prompt to be saved first. One branch, one PR, no self-merge. All four checks green per docs/MERGE-CHECKLIST.md.