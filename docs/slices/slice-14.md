# Slice 14 — Cloud adapters (Anthropic, OpenAI, Deepseek)

Branch: `slice-14` (from `main`). Scope: extend the gateway with three real cloud adapters so cloud models in the registry can actually complete. **Schema-free** (the `models` table and `call_logs` already carry every field needed; `api_model_id`, `input_cost_per_1k`, `output_cost_per_1k` were seeded in slice 04). The existing `compute_cost_sek` + `gateway_service` log/freeze cost path handles billing automatically once tokens come back. **Cloud models remain `enabled=False` by default** — user must explicitly enable in the Settings panel. **Out of scope: cost-ceiling enforcement (slice 15), embeddings via cloud, streaming responses, function calling.**

## In scope
1. **Anthropic adapter** — `app/gateway/anthropic.py`: implements the `Gateway` protocol. `complete(model, prompt, system?)` calls `POST https://api.anthropic.com/v1/messages` with:
   - Headers: `x-api-key: <config.anthropic_api_key>`, `anthropic-version: 2023-06-01`, `content-type: application/json`.
   - Body: `{ model: model.api_model_id, max_tokens, system, messages: [{role:'user', content: prompt}] }`.
   - Parse: `content[0].text` → text; `usage.input_tokens` → in_tokens; `usage.output_tokens` → out_tokens.
   - Error mapping: 401/403 → `GatewayError("authentication failed")`; 429 → `GatewayError("rate limited")`; 5xx → `GatewayError("provider unavailable")`; missing/invalid response shape → `GatewayError("malformed response")`. Missing API key → clear error before the HTTP call.

2. **OpenAI adapter** — `app/gateway/openai.py`: `complete(...)` calls `POST https://api.openai.com/v1/chat/completions`:
   - Headers: `Authorization: Bearer <config.openai_api_key>`, `Content-Type: application/json`.
   - Body: `{ model: model.api_model_id, max_tokens, messages: [{role:'system', content: system}, {role:'user', content: prompt}] }` (system only included if provided).
   - Parse: `choices[0].message.content` → text; `usage.prompt_tokens` → in_tokens; `usage.completion_tokens` → out_tokens.
   - Same error mapping pattern.

3. **Deepseek adapter** — `app/gateway/deepseek.py`: OpenAI-compatible. Either share code via an `OpenAICompatibleAdapter` base or subclass; key change is `base_url = https://api.deepseek.com/v1` and `config.deepseek_api_key`. Same parsing as OpenAI.

4. **Factory update** — `app/gateway/factory.py`: replace the three `GatewayError("adapter not implemented")` raises with real adapter instantiations. Lookup by `model.provider`. Pass the right API key + base URL to each.

5. **Cloud-specific resilience tweaks** — reuse `app/gateway/resilience.py` retry/timeout pattern, but:
   - Per-call timeout for cloud defaults to 60s (vs 120s for local) per REQ-ROUTER-014 (settings-driven, already in `settings`).
   - Skip the pre-call health check for cloud (a `GET /v1/models` roundtrip per call isn't worth it; let the actual call fail clearly).
   - Treat 429 as retryable (with backoff); treat 401/403 as immediately non-retryable (fail closed); treat 5xx as retryable.

6. **Config** — confirm `config.py` already exposes `anthropic_api_key`, `openai_api_key`, `deepseek_api_key` from `.env` (it should — slice-04 settings include these). If any of the three keys is missing, the relevant adapter fails clearly on first call (not at startup — the user might never enable cloud).

7. **Tests** (deterministic — no live cloud calls, ever):
   - Per-adapter (Anthropic, OpenAI, Deepseek): recorded/mocked HTTP responses via respx or httpx mocking — assert correct text + token parsing on success; assert each error path (401, 403, 429, 5xx, malformed body, network failure) raises a `GatewayError` with a clear, distinct message; assert missing API key raises before the HTTP attempt.
   - Factory: each provider value (`'anthropic'`, `'openai'`, `'deepseek'`) returns the correct adapter; unknown provider raises clearly.
   - End-to-end through `gateway_service.complete_model`: with a cloud model id and a fake cloud adapter injected, the existing flow logs `call_logs` with correct frozen cost (using the model's per-1k rates) and `provider` set to the cloud provider.
   - API: `POST /api/models/{id}/complete` for a cloud model (with fake gateway) returns 200; 502 surfaces on adapter failures; cloud-model-disabled still returns 409 (the existing slice-05 behavior).

## Out of scope (build NO behavior)
Cost-ceiling enforcement (slice 15), cloud embeddings (use local `nomic-embed-text`), Router ON / auto-routing, streaming responses, function calling / tool use, image inputs, system-prompt registry, frontend "enable cloud" warning dialog (defer to settings polish), per-provider rate-limit budgets, retry backoff tuning beyond the default pattern, classification using cloud models (defer).

## API shapes
- No API surface change. Cloud adapters fit the existing `Gateway` protocol and `gateway_service.complete_model` path. `GET /api/models` already returns cloud models; user enables them via the existing Settings panel (slice 04).

## Suggested file layout (one entity/function per file, ≤200 lines; keep adapters injectable)
Backend: `app/gateway/anthropic.py`, `app/gateway/openai.py`, `app/gateway/deepseek.py`, optionally `app/gateway/_openai_compatible.py` for shared OpenAI/Deepseek code; update `app/gateway/factory.py`. Tests: `test_gateway_anthropic.py`, `test_gateway_openai.py`, `test_gateway_deepseek.py`, extend `test_gateway_factory.py` for the new routing.
Frontend: **no changes** in this slice. Existing Test-a-model UI + generation/classify/inspect/blacklist UIs all work transparently with any enabled model.

## Acceptance criteria
- Enabling a seeded cloud model (e.g., Anthropic `claude-sonnet-4-20250514` or OpenAI `gpt-4o-mini`) in Settings + calling `POST /api/models/{id}/complete` produces a real response (token counts populated, `call_logs` row written with non-zero `cost_sek` per the model's rates, `provider` correctly set). **Smoke-test instructions live in the README under "Dev smoke: manual cloud completion" — do not run the live smoke in CI.**
- Adapter contract tests (mocked) cover success + every error-path mapping; factory routes correctly; gateway_service handles cloud the same way it handles Ollama.
- The previous "adapter not implemented" tests for cloud providers are **replaced** with success/failure tests; no test should still assert the not-implemented behavior.
- Cloud models remain `enabled=False` by default (no seed change); the registry seed must not flip them on.
- `pytest` + `pnpm test` pass with no live network access. Handoff in `docs/exchange/slice-14.md` with an acceptance-to-test mapping.

## Constraints
- Do not modify the schema or the slice-04 seed. Cloud models stay disabled by default. Do not read `.env` VALUES into your context — the config loads them at runtime. Use recorded/mocked HTTP fixtures for adapter tests; **never** make a live cloud call from a test. Keep the gateway dependency-injectable so service/API tests use fakes. Skip pre-call health-checks for cloud. Map 401/403 as non-retryable; 429/5xx as retryable. One branch, one PR, no self-merge.
