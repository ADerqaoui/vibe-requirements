# Slice 05 — LLM Gateway (local / Ollama)

Branch: `slice-05` (from `main`). Scope: a provider-agnostic LLM gateway with the **Ollama
(local)** adapter, manual model selection (Router OFF), the resilience layer, and call logging
with frozen cost. **Cloud adapters, auto-routing, and generation are later slices.** Design the
gateway interface so cloud adapters slot in later with no refactor.

## In scope
1. **Gateway interface** (`app/gateway/`): a `Gateway` protocol + `GatewayResult{text, in_tokens, out_tokens}` + `GatewayError`. A factory selects an adapter by `model.provider`. Ollama is implemented; `anthropic`/`openai`/`deepseek` raise a clear `GatewayError("adapter not implemented")` for now.
2. **Ollama adapter** — real `httpx` call to `http://localhost:11434` (`/api/chat`) using `model.ollama_tag`. Parse response text and tokens (`prompt_eval_count`→in_tokens, `eval_count`→out_tokens).
3. **Resilience** (settings-driven, REQ-ROUTER-013/14/17): lightweight health check before the call; retry up to `retry_count` (default 2) on error/timeout; per-call timeout (local default 120s). After retries, raise `GatewayError` (no auto model-fallback — that's Router ON, later).
4. **Gateway service + call logging** (REQ-ROUTER-019, REQ-COST-001..004): health → call (with retries) → cost via `compute_cost_sek` (slice 04), **freeze** `cost_sek` + `fx_rate` at call time → write a `call_logs` row (provider, model_id, in/out tokens, cost_sek, fx_rate, duration_ms, status, rendered_prompt, task='manual'). Log `status='failure'` on failure too.
5. **API** — `POST /api/models/{id}/complete` `{prompt, system?}` → `{text, in_tokens, out_tokens, cost_sek, duration_ms}`. 404 missing model; 409 disabled; 502 (clear message) on gateway failure after retries. Every outcome logs a `call_logs` row.
6. **Frontend** — a "Test a model" box: pick an enabled model, enter a prompt, send → show response text, tokens, cost (SEK), duration. (The manual Router-OFF path.)
7. **Tests** (deterministic — no live network in CI):
   - Ollama adapter: recorded/mocked HTTP responses → correct text + token parsing; malformed response → `GatewayError`.
   - Resilience: injected failures → retries `retry_count` times then raises; timeout path; health-check-fail → retry.
   - Service: with a **fake gateway** returning known tokens, assert a `call_logs` row with the correct **frozen** cost + fx_rate; a failing call logs `status='failure'`.
   - API: fake gateway injected → 200 with result + logged; 404 missing; 409 disabled; failure → 502 clear body.

## Out of scope (build NO behavior)
Cloud adapters (next slice), Router ON / auto model+prompt selection, generation/accept-reject, classification, inspector, blacklist, prompt-registry use, cost-ceiling enforcement (log cost, don't block).

## API shapes
- `CompletionRequest`: `{ prompt, system? }`.
- `CompletionResult`: `{ text, in_tokens, out_tokens, cost_sek, duration_ms }`.

## Suggested file layout (one entity/function per file, ≤200 lines; keep the gateway injectable)
Backend: `app/gateway/base.py`, `app/gateway/ollama.py`, `app/gateway/factory.py`, `app/gateway/resilience.py`, `app/services/gateway_service.py`, `app/schemas/completion.py`, `app/api/gateway.py` (register router), tests `test_gateway_ollama.py`, `test_gateway_resilience.py`, `test_gateway_service.py`, `test_gateway_api.py`.
Frontend: `src/api/gateway.ts`, `src/components/ModelTester.tsx`, wire into the panel, `ModelTester.test.tsx`.

## Acceptance criteria
- A real prompt to an enabled Ollama model returns text + token counts; a `call_logs` row is written with `cost_sek = 0` (local), `status='success'`, duration, rendered prompt.
- A cloud-provider model raises a clear "adapter not implemented" error (no crash) — covered by a test.
- Retries fire `retry_count` times on failure, then a clean `GatewayError`; failures logged `status='failure'`.
- Cost is frozen at call time (logged `cost_sek`/`fx_rate` unaffected by later rate/setting changes).
- `POST /api/models/{id}/complete`: 200 with result; 404 missing; 409 disabled; 502 on gateway failure.
- Frontend: pick a model, send a prompt, see response + tokens + cost + duration.
- `pytest` + `pnpm test` pass (no live network in CI). Handoff in `docs/exchange/slice-05.md` with an acceptance-to-test mapping.

## Constraints
- Do not read `.env` VALUES into your context (the app config loads them at runtime — that's fine). Do not modify the schema/migration. Keep the gateway dependency-injectable so service/API tests use a fake, not a live model. One branch, one PR, no self-merge.
