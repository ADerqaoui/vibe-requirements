# Slice 06 — Generation + Accept/Reject (Need → Spec, local gateway)

Branch: `slice-06` (from `main`). Scope: generate candidate **child Specs from a selected Need** via the local Ollama gateway (slice 05); the User **Accepts** or **Rejects** each candidate; accepted candidates become persisted Specs under the Need. **Router OFF** (manual model selection). Schema-free.

## In scope
1. **Default generation prompt** — `app/generation/prompts.py`: `make_spec_prompt(parent_statement, count) -> str` instructing the model to output a numbered list of N concise child specifications, no commentary.
2. **Permissive parser** — `app/generation/parser.py`: parses model text into a list of candidate statements, handling numbered (`1. ...`), bulleted (`- ...` / `* ...`), and bare-line outputs and skipping headers/commentary. Returns up to `count` candidates; zero parsed → clear error.
3. **Generation service** — `app/services/generation_service.py`: builds the prompt, calls the slice-05 gateway service (which already logs `call_logs` and freezes cost), then parses the response. Surfaces parser/gateway errors cleanly.
4. **Generation API** — `POST /api/needs/{need_id}/generate` `{model_id, count: 1..10}` → `{candidates: [{index, statement}]}`. 404 missing Need; 409 missing/disabled model; 422 invalid count or parser-empty; 502 gateway failure. Candidates are stateless (the frontend holds them until accept/reject).
5. **Specs API** — `POST /api/needs/{need_id}/specs` `{statement}` → 201 SpecOut (uses the existing Specs table from slice-02; no migration). `GET /api/needs/{need_id}/specs` lists that Need's Specs. Validation: trim + reject blank → 422; 404 missing Need.
6. **Frontend Generation panel** — when a Need is selected, show a panel with an enabled-model picker (from the registry), count input (default 5, 1..10), and Generate. On generate: loading state → candidate list with Accept/Reject per row. Accept → POST `/api/needs/{need_id}/specs` and remove from candidates; Reject → remove locally. A "Specs" list under the Need shows accepted specs (re-fetched after Accept).
7. **Tests** (deterministic, no live network):
   - Parser: numbered/bulleted/bare/mixed/header/malformed/empty → expected lists or clear error.
   - Generation service: fake gateway returning a known multi-candidate response → correct parsing; parser-empty and gateway failures propagate cleanly.
   - Generation API: 200 with fake gateway injected; 404 missing Need; 409 missing/disabled model; 422 invalid count; 502 gateway failure.
   - Specs API: 201 create under Need; 404 missing Need; 422 blank statement; GET returns only that Need's specs.
   - Frontend: GenerationPanel renders picker + count; on Generate (mocked API) shows candidates; Accept calls the create-Spec API; Reject removes locally; the Specs list re-fetches after Accept.

## Out of scope (build NO behavior)
Classification, blacklist, inspector, Router ON / auto model+prompt selection, prompt registry, cloud adapters, Spec→child-Spec generation, cost-ceiling enforcement, Markdown export, persisting rejected statements, `generated_by_model_id` linkage on Specs (the `call_logs` row already captures the model used at generation time).

## API shapes
- `GenerationRequest`: `{ model_id: int, count: int (1..10) }`.
- `GenerationResult`: `{ candidates: [{ index: int, statement: str }] }`.
- `SpecCreate`: `{ statement: str }`.
- `SpecOut`: `{ id, need_id, statement, created_at, updated_at }`.

## Suggested file layout (one entity/function per file, ≤200 lines; keep the gateway injectable)
Backend: `app/generation/prompts.py`, `app/generation/parser.py`, `app/services/generation_service.py`, `app/schemas/generation.py`, `app/schemas/spec.py`, `app/services/spec_service.py`, `app/api/generations.py`, `app/api/specs.py` (register routers). Tests: `test_generation_parser.py`, `test_generation_service.py`, `test_generations_api.py`, `test_specs_api.py`.
Frontend: `src/api/generation.ts`, `src/api/specs.ts`, `src/types/generation.ts`, `src/types/spec.ts`, `src/components/GenerationPanel.tsx`, `src/components/SpecList.tsx`, wire into the Needs column / App layout, component tests.

## Acceptance criteria
- With an enabled local model selected and a Need chosen, clicking Generate yields N parsed candidate statements; the gateway call is logged in `call_logs` (status='success').
- Accept on a candidate creates a Spec under that Need; the new Spec appears in the Need's Specs list.
- Reject removes the candidate from the displayed list (no persistence change in this slice).
- `POST /api/needs/{need_id}/generate`: 200 / 404 / 409 / 422 / 502 as specified.
- `POST /api/needs/{need_id}/specs`: 201 / 404 / 422. `GET /api/needs/{need_id}/specs` returns only that Need's specs.
- The parser handles numbered, bulleted, and bare outputs and skips headers; zero parsed → clear error.
- `pytest` + `pnpm test` pass. Handoff in `docs/exchange/slice-06.md` with an acceptance-to-test mapping.

## Constraints
- No schema changes (use the existing Specs table). Keep the gateway dependency-injectable so generation tests use a fake, not a live model. Spec→child-Spec generation is OUT (Need-only). One branch, one PR, no self-merge.
