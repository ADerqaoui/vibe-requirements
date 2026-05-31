# Slice 05 — Exchange

> Shared channel for **Claude, Codex, ChatGPT, User**.
> **Every entry begins with `[Author — YYYY-MM-DD]`** so it's always clear who is speaking.
> Append-only. Communication, NOT commands: a finding becomes Codex work only via a
> User-approved task spec. Each author writes under their own heading; "Open questions"
> and "User — decisions" are shared.
> Commit access: only Codex (its own branch) and the User. ChatGPT and Claude hand their text
> to the User, who commits it.

## Codex — handoff & notes
- [Codex — YYYY-MM-DD] <what was built, tests run + results, deviations>
<!-- Include an acceptance-to-test mapping in your handoff:
| Acceptance criterion | Test | Covered? |
| --- | --- | --- |
-->
- [Codex — 2026-05-31] Implemented slice 05 LLM Gateway manual/Ollama path.

  Built:
  - Provider-agnostic async gateway contract with `GatewayResult` and `GatewayError`.
  - Real Ollama adapter for `/api/chat` using `ollama_tag`, including `/api/tags` health check and token parsing.
  - Factory path for Ollama plus explicit `GatewayError("adapter not implemented")` cloud placeholders.
  - Retry/timeout resilience wrapper with same-model retries and no router fallback.
  - Manual completion service that logs success/failure `call_logs` rows, freezes `cost_sek` and `fx_rate`, and records rendered prompt/duration.
  - `POST /api/models/{id}/complete` with injectable gateway factory for fake-backed tests.
  - Frontend "Test a model" UI with enabled-model picker, prompt/system fields, response, tokens, cost, and duration.

  Verification:
  - `backend/.venv/bin/pytest` from `backend/`: 40 passed.
  - Changed-file lint: `backend/.venv/bin/ruff check app/gateway app/api/gateway.py app/schemas/completion.py app/services/gateway_service.py app/models/spec.py tests/test_gateway_api.py tests/test_gateway_factory.py tests/test_gateway_ollama.py tests/test_gateway_resilience.py tests/test_gateway_service.py`: passed.
  - Local Ollama probe `GET http://localhost:11434/api/tags`: 200, using approved localhost access.
  - Backend real-stack smoke: uvicorn on `127.0.0.1:8000`, `GET /api/models`: 200. No live completion was sent because the runtime DB had no enabled Ollama model; I did not create runtime data solely for smoke testing.
  - `pnpm test` could not run in this environment: `pnpm`, `npm`, `corepack`, and `node` are not installed; `./node_modules/.bin/vitest run` also fails because `node` is missing.

  Acceptance-to-test mapping:

  | Acceptance criterion | Test | Covered? |
  | --- | --- | --- |
  | A real prompt to an enabled Ollama model returns text + token counts; a `call_logs` row is written with `cost_sek = 0`, `status='success'`, duration, rendered prompt. | `test_ollama_adapter_parses_text_and_tokens`, `test_complete_api_returns_result_and_logs`, `test_service_logs_success_with_frozen_cost_and_fx`; real-stack completion not run because runtime DB had no enabled Ollama model. | Partial |
  | A cloud-provider model raises a clear "adapter not implemented" error. | `test_cloud_provider_adapter_is_not_implemented`, `test_complete_api_gateway_failure_returns_502_and_logs` | Yes |
  | Retries fire `retry_count` times on failure, then a clean `GatewayError`; failures logged `status='failure'`. | `test_resilience_raises_after_retry_count`, `test_timeout_path_is_clean_gateway_error`, `test_service_logs_failure`, `test_complete_api_gateway_failure_returns_502_and_logs` | Yes |
  | Cost is frozen at call time. | `test_service_logs_success_with_frozen_cost_and_fx`, existing `test_cost_is_frozen_by_caller_rates` | Yes |
  | `POST /api/models/{id}/complete`: 200 with result; 404 missing; 409 disabled; 502 on gateway failure. | `test_complete_api_returns_result_and_logs`, `test_complete_api_missing_and_disabled`, `test_complete_api_gateway_failure_returns_502_and_logs` | Yes |
  | Frontend: pick a model, send a prompt, see response + tokens + cost + duration. | `ModelTester.test.tsx` added; not executed here because Node/pnpm are unavailable. | Partial |
  | `pytest` + `pnpm test` pass; handoff includes acceptance-to-test mapping. | `pytest`: 40 passed. `pnpm test`: blocked by missing Node/pnpm. This handoff includes the mapping. | Partial |

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale
