# Slice 16 — Prompt registry (DB-backed, versioned, audit-wired)

Branch: `slice-16` (from `main`). Scope: move the four hardcoded prompts (Need→Spec generation, Spec→child generation, classification, inspection) from code into the existing `prompts` table, add a small lookup/render service, replace the in-code prompt strings at the four call sites, and wire `call_logs.prompt_id` + `prompt_version` so every paid or free call is traceable to the exact prompt that produced it. Read-only **Prompts panel** in Settings. **Schema-free** — `prompts` table and `call_logs.prompt_id`/`prompt_version` columns already exist from slice 1.

## In scope

1. **Seed four prompts** into the `prompts` table (idempotent — re-running the seed must not duplicate or revert manual edits). Recommended task names (Codex may finalize, must stay consistent across DB + code):
   - `generate_need_to_spec` — current hardcoded slice-6 prompt
   - `generate_spec_to_child` — current hardcoded slice-9 prompt
   - `classify_spec` — current hardcoded slice-7 prompt
   - `inspect_spec` — current hardcoded slice-10 prompt
   Each seeded with `version=1`, `enabled=1`, `layer_id=NULL`, `discipline_scope=NULL`, and a clear `name` + `description`. **Templates must be the exact strings currently hardcoded in code** so behavior is byte-identical pre- and post-slice. Use `{var}` placeholders for runtime substitution (the existing prompts already do this in code or near enough — preserve the placeholder names).

2. **prompt_service** (`app/services/prompt_service.py`):
   - `get_active(task: str) -> Prompt` — returns the highest `version` row matching `task` with `enabled=1`. Raises a clear `PromptNotFoundError` if none. For slice 16, ignores `layer_id` and `discipline_scope` (always falls back to NULL); pluggable so future slices can extend.
   - `render(task: str, **vars) -> RenderedPrompt(text, prompt_id, prompt_version)` — looks up the active prompt and calls `template.format(**vars)`. Missing variable raises a clear `PromptVariableMissingError(var_name)` (not the raw KeyError). Returns the rendered text **plus** the prompt id + version so the caller can write them to `call_logs`.
   - Keep it under ~80 lines. No caching (DB lookups are tiny and we want edits to take effect immediately when prompt editing lands).

3. **Replace hardcoded prompts at four call sites**:
   - `generation_service` (slice 6 Need→Spec, slice 9 Spec→child) — call `prompt_service.render('generate_need_to_spec', need_statement=...)` or `'generate_spec_to_child'`; pass the returned prompt_id + version through to the gateway call.
   - `classification_service` — call `prompt_service.render('classify_spec', spec_statement=...)`.
   - `inspector_service` — call `prompt_service.render('inspect_spec', spec_statement=...)`.
   Each service must pass `prompt_id` + `prompt_version` through to `gateway_service.complete_model` so they reach `call_logs`. Existing hardcoded strings are deleted, not kept as a fallback — the DB is the source of truth.

4. **Wire `call_logs.prompt_id` + `prompt_version`**: `gateway_service.complete_model` accepts optional `prompt_id` + `prompt_version` parameters (default NULL, so the existing `models/{id}/complete` manual completion endpoint can pass nothing). When provided, they're written to the `call_logs` row alongside `cost_sek`, etc. Free-form manual completion (no prompt) keeps writing NULL — that's expected and fine.

5. **GET /api/prompts** — returns the list of currently active prompts (one per task, the highest enabled version). Shape:
```json
   [
     { "task": "generate_need_to_spec", "name": "...", "description": "...", "version": 1, "layer_id": null, "discipline_scope": null, "template": "...", "updated_at": "..." },
     ...
   ]
```
   Read-only endpoint; no POST/PUT/DELETE this slice.

6. **Frontend Prompts panel** (read-only) inside Settings, after the existing sections:
   - New `frontend/src/components/PromptsPanel.tsx` fetches `/api/prompts` on mount and renders each prompt as: task name + version + layer/discipline (showing "any" when null) + a collapsible/scrollable `<pre>`-style block showing the template, plus updated_at.
   - Note: not all prompts are short. Keep the template area collapsible so the panel doesn't dominate Settings.
   - **No editing.** A small inline note: "Editable in a future slice."

7. **Tests** (deterministic):
   - **prompt_service**: `get_active` returns the highest enabled version. Missing task → `PromptNotFoundError`. `render` substitutes correctly. Missing variable → `PromptVariableMissingError` with the variable name (not raw KeyError).
   - **Seed**: running the seed once writes four rows; running it twice doesn't duplicate; pre-existing `enabled=0` or higher-version rows are preserved (idempotency is content-aware — match on task+version, don't blindly upsert by task).
   - **generation/classification/inspection**: existing tests still pass byte-identical (template strings unchanged). NEW assertion: after a successful call, the most recent `call_logs` row has `prompt_id` and `prompt_version` set to the active prompt's values.
   - **API**: `GET /api/prompts` returns the four seeded prompts in stable order; `version` and `template` match the seeded values.
   - **Frontend**: `PromptsPanel` renders with mocked API data — each task appears, version shows, template content is present.

## Out of scope (build NO behavior)
Prompt editing UI (create / update / promote-to-active), prompt rollback, layer-aware or discipline-aware lookup (deferred to V-model navigator slice), prompt A/B testing or randomized routing, per-project prompt overrides, prompt import/export, prompt diff view between versions, prompt usage statistics in CostPanel/elsewhere, dynamic template engine (Jinja2 etc. — stick with `str.format`).

## API shapes
- `GET /api/prompts` (new — read-only list, shape above).
- `POST /api/models/{id}/complete`: behavior unchanged (still no `prompt_id`/`prompt_version` written for manual completions).
- Generation, classification, inspection endpoints: API surface unchanged externally; internally now route through `prompt_service.render` and pass prompt id+version through to `call_logs`.
- No schema migration.

## Suggested file layout (one entity per file, ≤200 lines)
Backend: `app/services/prompt_service.py` (new, ~80 lines), `app/services/prompt_errors.py` or extend an existing errors module — small typed exceptions (`PromptNotFoundError`, `PromptVariableMissingError`), `app/schemas/prompt.py` (Pydantic Out schema for GET endpoint), `app/api/prompts.py` (read-only route), updates to `app/services/generation_service.py`, `classification_service.py`, `inspector_service.py`, `gateway_service.py` (signature accepts optional `prompt_id`/`prompt_version`), updates to the seed (`app/seed/run.py` or equivalent) to insert the four prompts. Tests: `test_prompt_service.py`, `test_prompts_api.py`, additions to existing service/integration tests for the prompt_id/prompt_version assertion.
Frontend: `frontend/src/components/PromptsPanel.tsx`, `frontend/src/api/prompts.ts` (small), `frontend/src/types/prompt.ts`, integration into `SettingsPanel.tsx` (keep SettingsPanel under 200 lines — extract PromptsPanel rendering, don't inline). Tests: `PromptsPanel.test.tsx`.

## Acceptance criteria
- The four prompts exist as DB rows after seeding; deleting any of them and re-running the seed restores it (idempotent re-add of missing rows).
- Behavior of generation, classification, and inspection is byte-identical pre- and post-slice (templates unchanged when stored in DB).
- Every successful generation/classification/inspection writes a `call_logs` row with non-null `prompt_id` and `prompt_version` matching the active prompt for that task.
- `GET /api/prompts` returns the four active prompts.
- Settings shows a read-only Prompts panel with each prompt's name/version/template visible (or expandable). Both `GenerationPanel.tsx` and `SettingsPanel.tsx` remain strictly under 200 lines.
- `pytest` + `pnpm test` pass. Handoff in `docs/exchange/slice-16.md` with acceptance-to-test mapping.

## Constraints
- Schema-free. Do not modify `prompts` columns. Do not add a migration. Do not introduce a new template engine — `str.format` only. Do not cache prompt lookups. Do not change the existing prompt text — copy it byte-for-byte from the call sites into the seed. The four task names chosen are stable identifiers; once seeded, code references them as string literals (it's fine to centralize them as constants in `prompt_service.py`). One branch, one PR, no self-merge.
