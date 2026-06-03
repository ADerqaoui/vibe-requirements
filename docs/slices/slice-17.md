# Slice 17 — Prompt editing (versioned, validated, with the Spec→child wording fix)

Branch: `slice-17` (from `main`). Scope: make the prompt registry editable. Editing creates a new immutable version (history preserved so old `call_logs` still point to the exact version that produced them); promote/rollback re-activates any historical version; templates are validated against a per-task variable contract at save time; all `str.format` failures become typed errors; and the deferred Spec→child "Need:" wording bug is fixed through the new versioning path. Editable Prompts panel with per-task version history. **Schema-free** — the `prompts` table already supports versioning (no UNIQUE constraint on task; `version`, `enabled`, `updated_at` all present).

## Versioning model (immutable versions)
- A "task" has N rows, one per version. Exactly one row per task has `enabled=1` (the active version). Invariant maintained by create + promote.
- **Edit** = insert a NEW row: `version = max(version for task) + 1`, `enabled=1`; set `enabled=0` on the previously-active row for that task. Existing rows are never mutated (immutability keeps `call_logs.prompt_id`/`prompt_version` audit trail valid forever).
- **Promote / rollback** = set `enabled=1` on a chosen historical row, `enabled=0` on all other rows for that task.
- `get_active` is unchanged (highest enabled version); after a rollback to v1 with v2 disabled, `get_active` returns v1 — verify this holds.

## Per-task variable contract (for save-time validation)
Derived from the actual render call sites — do not change these:
- `generate_need_to_spec` → exactly `{parent_statement}`, `{count}`
- `generate_spec_to_child` → exactly `{parent_statement}`, `{count}`
- `classify_spec` → exactly `{spec_statement}`
- `inspect_spec` → exactly `{spec_statement}`
Define this contract as a mapping in a new `app/services/prompt_validation.py` (or in `prompt_service`). Tasks are fixed by code; the endpoint must reject unknown tasks.

## In scope

1. **Template validation** (`prompt_validation.validate_template(task, template)`):
   - Parse placeholders with `string.Formatter().parse(template)`. Malformed braces raise `ValueError` → catch and raise typed `PromptTemplateInvalidError("malformed braces")`.
   - Collect the set of named field names used. Require **used == required** for the task: every required variable present, and no unknown variables (unknown vars would `KeyError` at render). On mismatch raise `PromptTemplateInvalidError` with a message naming the missing and/or unexpected variables.
   - Reject positional/empty fields (`{}`, `{0}`) and any field with a conversion (`!r`) or non-empty format spec (`:>10`) — templates must be plain named substitution only. Raise `PromptTemplateInvalidError` with the offending token.
   - Reject empty/whitespace-only template.

2. **Typed errors** (extend `app/services/prompt_errors.py`):
   - `PromptTemplateInvalidError(reason)` — validation failure on save → HTTP 422.
   - `PromptRenderError(reason)` — render-time `ValueError`/`IndexError` (defense-in-depth; validation should prevent it) → HTTP 500. Update `prompt_service.render` to catch `ValueError`/`IndexError` (in addition to the existing `KeyError → PromptVariableMissingError`) and raise `PromptRenderError`.

3. **prompt_service additions** (keep functions small, transactional):
   - `create_version(db, task, template, name=None, description=None) -> Prompt`: validate first (raises on invalid); require the task to already exist (else `PromptNotFoundError`); compute next version; carry over `name`/`description`/`layer_id`/`discipline_scope` from the current active version when omitted; insert `enabled=1`; disable the prior active row; commit atomically (rollback both writes on failure).
   - `promote(db, prompt_id) -> Prompt`: load the row (404 → raise a typed not-found); set `enabled=1` on it and `enabled=0` on all other rows for the same task; commit atomically.
   - `list_versions(db, task) -> list[Prompt]`: all versions for a task, newest first (version desc, id desc).

4. **API** (`app/api/prompts.py`, extend):
   - `GET /api/prompts` — unchanged (active list).
   - `GET /api/prompts/{task}/versions` — full version history for a task (id, version, enabled, name, description, template, created_at, updated_at). 404 if task unknown.
   - `POST /api/prompts/{task}/versions` — body `{ template, name?, description? }`. 200 with the new active prompt; 422 (`PromptTemplateInvalidError`) with `{ error: "prompt_template_invalid", reason }`; 404 if task unknown.
   - `POST /api/prompts/{id}/promote` — 200 with the promoted prompt; 404 if id unknown.

5. **Spec→child wording fix (the deliberate behavior change, delivered via versioning)**:
   - Add a corrected `generate_spec_to_child` **version 2** to the seed, with Spec-appropriate wording and the SAME variables `{parent_statement}` + `{count}` (so the render call site is untouched):
     ```
     Generate child specifications for this parent specification.
     Parent specification: {parent_statement}
     Output exactly {count} concise child specifications.
     Use a numbered list. Do not include commentary, headings, or explanations.
     ```
   - Seed corrective logic (idempotent, one-time): if `generate_spec_to_child` has no `version=2` row, insert v2 (`enabled=1`) and set its `version=1` row to `enabled=0`. If v2 already exists, do nothing (respects any later manual promote/rollback the user made). Do NOT touch `generate_need_to_spec` (its v1 stays active and unchanged).
   - This is the canonical "first real edit," exercising the versioning path end-to-end while fixing the latent bug — auditable (v1 preserved) and reversible (promote v1 via the UI).

6. **Frontend — editable Prompts panel**:
   - `PromptEditor.tsx`: opened from a task's "Edit" button; textarea prefilled with the active template, plus optional name/description fields; Save → `POST /api/prompts/{task}/versions`; show 422 `reason` inline; on success refresh and close.
   - `PromptHistory.tsx`: opened from a task's "History" button; lists versions (version, enabled badge, created_at, collapsible template); "Promote" button on non-active versions → `POST /api/prompts/{id}/promote` → refresh.
   - `PromptsPanel.tsx`: orchestrates; remove the slice-16 "Editable in a future slice" note; refresh after edit/promote.
   - Keep every touched file strictly under 200 lines (extract editor + history as separate components; do not inline into PromptsPanel or SettingsPanel).

7. **Tests** (deterministic):
   - **prompt_validation**: valid template passes; missing required var rejected; unknown var rejected; malformed braces rejected; positional/empty field rejected; conversion/format-spec rejected; empty template rejected — each raises `PromptTemplateInvalidError` with a useful message.
   - **prompt_service**: `create_version` computes next version, flips enabled atomically, carries over name/description when omitted, validates before writing (invalid → no row written); `promote` flips enabled across siblings; unknown task/id raise typed errors; `get_active` returns the enabled row even when a higher disabled version exists (rollback case); `render` maps `ValueError` → `PromptRenderError`.
   - **seed corrective**: fresh seed → `generate_spec_to_child` v2 active with corrected wording + v1 present but disabled; re-running seed is a no-op (v2 already exists); v2 template contains "parent specification" and NOT "Need:"; `generate_need_to_spec` v1 still active and unchanged. Update the slice-16 equality assertion: v1 templates of the two generation tasks remain identical (history), but the ACTIVE `generate_spec_to_child` (v2) differs from `generate_need_to_spec` and is the corrected text.
   - **generation integration**: spec→child generation now renders the v2 wording (assert the rendered prompt contains "Parent specification:"); need→spec unchanged. (Mock the gateway — no live calls.)
   - **API**: POST versions success + 422 invalid + 404 unknown task; promote success + 404 unknown id; versions list shape + ordering.
   - **frontend**: PromptEditor prefilled + save + inline 422 error; PromptHistory lists + promote; PromptsPanel refreshes after each.

## Out of scope (build NO behavior)
Layer/discipline-aware lookup or editing those fields (still deferred to the V-model navigator slice — leave `layer_id`/`discipline_scope` NULL and not user-editable), per-project prompt overrides, A/B testing / randomized routing, version diff view (defer), prompt import/export, creating brand-new tasks via the API (tasks are fixed by code call sites), prompt usage statistics, a different template engine (still `str.format`).

## API shapes
- `GET /api/prompts/{task}/versions` (new), `POST /api/prompts/{task}/versions` (new, 200/422/404), `POST /api/prompts/{id}/promote` (new, 200/404). `GET /api/prompts` unchanged. No schema migration.

## Suggested file layout (one entity per file, ≤200 lines)
Backend: `app/services/prompt_validation.py` (new), extend `app/services/prompt_errors.py` (+2 errors), extend `app/services/prompt_service.py` (create_version/promote/list_versions/render-hardening), `app/schemas/prompt.py` (version create body + version-list out), extend `app/api/prompts.py`, update the prompt seed for the v2 corrective. Tests: `test_prompt_validation.py`, extend `test_prompt_service.py`, extend `test_prompts_api.py`, extend `test_seed.py` and the generation integration test.
Frontend: `frontend/src/components/PromptEditor.tsx`, `frontend/src/components/PromptHistory.tsx`, extend `frontend/src/api/prompts.ts` + `frontend/src/types/prompt.ts`, slim `PromptsPanel.tsx`. Tests: `PromptEditor.test.tsx`, `PromptHistory.test.tsx`, extend `PromptsPanel.test.tsx`.

## Acceptance criteria
- Editing a prompt in Settings creates a new active version; the prior version remains in history and is promotable.
- Saving an invalid template (missing/unknown variable, malformed braces, format spec) is rejected with a clear inline reason; no row is written.
- After this slice, Spec→child generation uses the corrected "Parent specification:" wording (v2 active); Need→Spec is unchanged; v1 of Spec→child is preserved and can be promoted back.
- Old `call_logs` rows still reference valid, unchanged prompt versions (immutability holds).
- All touched frontend files stay strictly under 200 lines.
- `pytest` + `pnpm test` pass. Handoff in `docs/exchange/slice-17.md` with acceptance-to-test mapping.

## Constraints
- Schema-free; no migration; no UNIQUE assumptions added. Immutable versions — never UPDATE a template in place; always insert a new version. Maintain the one-enabled-per-task invariant in both create and promote, transactionally. `str.format` only. Tasks fixed by code; reject unknown tasks. Seed corrective for v2 must be idempotent and must not override a user's later promote choice. One branch, one PR, no self-merge.
