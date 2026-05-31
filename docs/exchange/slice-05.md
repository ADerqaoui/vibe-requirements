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
- [Codex — 2026-05-31] Follow-up per user request: added API coverage for whitespace-only prompts on `POST /api/models/{id}/complete` asserting `422`, and documented the dev-only manual Ollama completion curl smoke command in `README.md`. Verification: `backend/.venv/bin/pytest` from `backend/` collected 41 tests and passed (`41 passed, 29 warnings`).

## ChatGPT — QA review
- [ChatGPT — 2026-05-31] Verdict: BLOCK.

  Findings:

  1. Category: Risk
     Severity: major
     Location: PR #4 status / GitHub metadata
     What's wrong and why it matters: The PR is still marked as a draft. Draft status usually means the implementer has not declared the work ready for final review/merge. Even though the branch is clean against `main` and GitHub reports it as mergeable, QA should not approve a draft PR as merge-ready.
     Suggested check or fix: Mark the PR ready for review only after the implementer confirms the slice is final and all required validation is complete.

  2. Category: Missing test
     Severity: major
     Location: `docs/exchange/slice-05.md` — Codex handoff / Verification
     What's wrong and why it matters: Slice 05 acceptance requires `pytest` and `pnpm test` to pass. The handoff says backend `pytest` passed, but `pnpm test` could not run because Node/pnpm are unavailable in the environment. This leaves the frontend `ModelTester` acceptance path unverified by executed tests.
     Suggested check or fix: Run `pnpm test` in an environment with Node/pnpm installed and record the result in the handoff. If it fails, fix the frontend tests before requesting approval.

  3. Category: Missing test
     Severity: major
     Location: `docs/exchange/slice-05.md` — Acceptance-to-test mapping; Slice 05 acceptance criterion for real Ollama prompt
     What's wrong and why it matters: The handoff marks the real enabled-Ollama completion acceptance as only partially covered. Slice 05 explicitly requires a real prompt to an enabled Ollama model to return text and token counts and write a `call_logs` success row with local cost zero. The PR includes mocked/deterministic coverage, which is good, but the real-stack acceptance path was not executed because the runtime DB had no enabled Ollama model.
     Suggested check or fix: Run one controlled local manual completion against an enabled Ollama model in a disposable/dev DB, then verify the response and the `call_logs` row. Record the exact smoke result in the handoff. Do not mutate production data.

  4. Category: Missing test
     Severity: minor
     Location: `backend/tests/test_gateway_api.py` / `backend/app/schemas/completion.py`
     What's wrong and why it matters: The completion request schema trims and rejects blank prompts, but the API tests do not directly cover blank/whitespace prompt rejection. This is not a core slice acceptance item, but it is an important input-validation edge case for a public LAN endpoint.
     Suggested check or fix: Add an API test for `POST /api/models/{id}/complete` with `"prompt": "   "` and assert `422`.

  5. Category: Risk
     Severity: minor
     Location: `frontend/src/components/SettingsPanel.tsx`
     What's wrong and why it matters: `SettingsPanel.tsx` is now 228 lines and continues to grow as more model/gateway behavior is added. It remains below the hard 300-line split threshold, but above the project convention target of 200 lines and now includes the `ModelTester` wiring in addition to model/settings CRUD.
     Suggested check or fix: No immediate blocker by itself. Consider splitting model registry, settings, and tester sections before router/model-selection behavior grows further.

  Things that look fine:

  * The Slice 05 branch is clean against current `main`: it is ahead by two commits and not behind.
  * The diff appears scoped to the local/Ollama gateway path, gateway service, completion API, call logging, frontend tester, tests, and Slice 05 docs.
  * No schema or Alembic migration files appear in the Slice 05 delta.
  * Cloud providers intentionally return `GatewayError("adapter not implemented")`, matching the slice.
  * The Ollama adapter uses mocked HTTP tests for response parsing and malformed payload handling.
  * Service tests cover success logging, frozen cost/fx behavior, and failure logging.
  * API tests cover 200 success, 404 missing model, 409 disabled model, and 502 gateway failure.
  * I did not see `.env`, database dumps, SQLite files, SQL dumps, or committed secret material in the reviewed Slice 05 delta.
  * I did not see out-of-scope generation, classification, inspector, blacklist, prompt-registry behavior, or router auto-selection implemented.

  Design concerns for the architect:

  1. Prompt logging is implemented as storing the rendered prompt in `call_logs.rendered_prompt`, which matches the slice, but this will become sensitive project data as real requirements are entered. The architect may want a later explicit retention/privacy rule before backups/export are added.
  2. The local real-stack acceptance step needs a repeatable dev-only procedure. The slice asks for a real Ollama path, but deterministic CI should not depend on a live model. A documented smoke-test command or fixture would reduce ambiguity.

  Open questions:

  * [ChatGPT — 2026-05-31] For the User/Codex: Should PR #4 remain blocked until `pnpm test` is run and recorded?
  * [ChatGPT — 2026-05-31] For the User/Codex: Should the real enabled-Ollama smoke test be required before marking Slice 05 ready for merge?


## Claude — conformance review & design notes
- [Claude — 2026-05-31] APPROVE on substance — verified gateway service (logs success+failure, frozen cost/fx), completion schema (blank→422 implemented), clean ahead-only delta, all 5 gateway test files present. Concur with ChatGPT: BLOCK is verification gaps, not code. F2 (pnpm test) and F3 (real Ollama smoke) to be run on the server and recorded; F4 (blank-prompt API test) + DC2 (documented dev smoke) as a tiny followup; F5 (SettingsPanel split) deferred. DC1 (rendered_prompt retention) deferred to the export/backup slice.

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale

## User — verification
- [User — 2026-05-31] F2 `pnpm test`: <PASTE pass/fail summary, e.g. "6 passed">.
- [User — 2026-05-31] F3 real Ollama smoke: POST /api/models/<ID>/complete returned text + tokens, cost_sek 0, status success. Response: <PASTE the JSON>.
