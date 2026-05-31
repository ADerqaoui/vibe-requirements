# Slice 07 — Classification (3-local-model vote on complexity 1–5)

Branch: `slice-07` (from `main`). Scope: classify a Spec's **complexity (1–5)** via parallel votes from three local models (`qwen2.5:7b`, `llama3.1:8b`, `gemma2:9b`), aggregated by **median**, persisted in `specs.complexity`. Router OFF (the three classification models are looked up from the registry by `ollama_tag`). Schema-free.

## In scope
1. **Classification prompt** — `app/classification/prompts.py`: `make_complexity_prompt(spec_statement) -> str` that asks for a single integer 1–5 (1=trivial … 5=very complex), no commentary.
2. **Vote parser** — `app/classification/parser.py`: `parse_complexity_vote(text) -> int`. Extracts the first digit 1–5 from the model's response (tolerant of "3", "I'd say 3", "Complexity: 4"). Raises a clear error if no valid digit.
3. **Classification service** — `app/services/classification_service.py`: looks up the three required models by `ollama_tag` (`qwen2.5:7b`, `llama3.1:8b`, `gemma2:9b`) and `enabled=True`; calls the slice-05 gateway service in parallel (`asyncio.gather`) for each; parses each vote; aggregates by **median** (sorted middle of three integers); persists to `specs.complexity` and bumps `updated_at`. If any required model is missing/disabled, raises a clear error **before** any gateway call (no partial-state writes). Each model call already logs to `call_logs` via the gateway service.
4. **API** — `POST /api/specs/{spec_id}/classify` → `{ spec_id, votes: [{ model_id, vote }], complexity }`. 404 missing Spec; 409 if any required classification model missing/disabled; 502 if **any** of the three gateway calls fails (no partial-vote tolerance in this slice).
5. **Frontend** — add a **Classify** button on each Spec in `SpecList`. On click: call the API, show a loading state, then render a small **complexity badge** (1–5) on the Spec. Specs without a complexity show "—". Hovering the badge tooltips the per-model votes.
6. **Tests** (deterministic):
   - Parser: digit alone, embedded digit, two digits (take first 1–5), out-of-range, no digit → expected int or clear error.
   - Classification service: three fake gateways returning known integers → correct median; missing/disabled required model → clear error and zero gateway calls; one gateway failing → API 502 (no partial vote).
   - API: 200 with three fake gateways; 404 missing Spec; 409 missing classification model; 502 on gateway failure.
   - Frontend: Classify button calls the API (mocked), badge renders with the returned complexity; tooltip lists per-model votes.

## Out of scope (build NO behavior)
Auto-classify on Accept (manual button only this slice), classification of Needs (Specs only), Router ON / auto model+prompt selection, cost-ceiling enforcement (calls still log cost via the gateway service), setting-driven classification model set, embedding-based blacklist, inspector, Spec→child-Spec generation, cloud adapters.

## API shapes
- `ClassificationResult`: `{ spec_id: int, votes: [{ model_id: int, vote: int }], complexity: int }`.

## Suggested file layout (one entity/function per file, ≤200 lines; keep the gateway injectable)
Backend: `app/classification/prompts.py`, `app/classification/parser.py`, `app/services/classification_service.py`, `app/schemas/classification.py`, `app/api/classification.py`. Tests: `test_classification_parser.py`, `test_classification_service.py`, `test_classification_api.py`.
Frontend: `src/api/classification.ts`, `src/types/classification.ts`, extend `src/components/SpecList.tsx` with Classify button + badge + tooltip (split if it crosses 200 lines), update `SpecList.test.tsx`.

## Acceptance criteria
- Clicking Classify on a Spec calls three local models in parallel, parses three votes, and persists the median in `specs.complexity`; three `call_logs` success rows are written.
- If any of the three classification models is missing or disabled in the registry, the API returns 409 with a clear message and makes no gateway calls.
- If any of the three gateway calls fails, the API returns 502 with a clear message (no partial-vote tolerance).
- The complexity badge appears on the Spec; tooltip shows per-model votes.
- `pytest` + `pnpm test` pass. Handoff in `docs/exchange/slice-07.md` with an acceptance-to-test mapping.

## Constraints
- No schema changes (`specs.complexity` already exists as INTEGER 1..5). Keep the gateway dependency-injectable so service/API tests use fakes, not live models. Classification applies to Specs only. The three classification model `ollama_tag`s are hardcoded constants — moving to settings is a later slice. One branch, one PR, no self-merge.
