# Slice 14 — Exchange

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

[Codex — 2026-06-02] Implemented schema-free cloud gateway adapters for Anthropic, OpenAI, and Deepseek. The factory now routes cloud providers to concrete adapters, cloud adapters skip pre-call health checks, missing keys/model ids fail before HTTP, 401/403 are non-retryable auth failures, 429/5xx are retryable, malformed responses produce clear `GatewayError`s, and OpenAI/Deepseek share an OpenAI-compatible adapter. Added README dev-only curl smoke instructions. No seed changes; cloud models remain disabled by default.

| Acceptance criterion | Test | Covered? |
| --- | --- | --- |
| Enabling a cloud model and calling `/api/models/{id}/complete` can produce a response, token counts, non-zero cost, and a cloud-provider `call_logs` row. | `backend/tests/test_gateway_api.py` — `test_complete_api_cloud_model_uses_cloud_timeout_and_logs`; `backend/tests/test_gateway_service.py` — `test_service_logs_success_with_frozen_cost_and_fx` | Yes |
| Manual cloud smoke instructions are documented and not run in CI. | `README.md` — `Dev smoke: manual cloud completion`; no live smoke run | Yes |
| Anthropic adapter success and error-path mappings are mocked, with no live cloud calls. | `backend/tests/test_gateway_anthropic.py` | Yes |
| OpenAI adapter success and error-path mappings are mocked, with no live cloud calls. | `backend/tests/test_gateway_openai.py` | Yes |
| Deepseek adapter success and error-path mappings are mocked, with no live cloud calls. | `backend/tests/test_gateway_deepseek.py` | Yes |
| Factory routes `anthropic`, `openai`, and `deepseek` to real adapters and rejects unknown providers. | `backend/tests/test_gateway_factory.py` | Yes |
| Previous cloud "adapter not implemented" behavior is removed from factory/tests. | `grep -R "adapter not implemented\|NotImplementedGateway" backend/app backend/tests README.md` -> no matches | Yes |
| Cloud models remain `enabled=False` by default; seed unchanged. | Existing `backend/tests/test_models.py` — `test_seed_models_and_settings_is_idempotent`; no changes to `backend/app/seed/models_seed.py` | Yes |
| `pytest` and `pnpm test` pass with no live network access. | `cd backend && .venv/bin/pytest` -> 147 passed; `cd frontend && PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` -> 24 passed | Yes |

[Codex — 2026-06-02] Tightening per QA F1+F2: invalid JSON now maps to non-retryable 'malformed response' instead of retryable 'request failed'. Resolves Open Question: invalid JSON = non-retryable.

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale

## Claude — final conformance
- [Claude — 2026-06-02] APPROVE — slice scope met; cloud spend is now mechanically possible. Adapter contract is tight: shared OpenAI-compatible base for OpenAI/Deepseek is the right factoring (single point of change for header/auth quirks); Anthropic stays separate because the API shape differs. Retryability discipline is consistent: only transient classes retry, everything that won't change on retry fails fast — including the F1+F2 fix making invalid JSON non-retryable. Pre-call health-check skip for cloud is the correct trade (saves one roundtrip per call; cloud is generally available; real failures surface via the actual call). Frontend correctly required zero changes — proves the slice-04 model-registry abstraction held. Open question on invalid JSON resolved in the tightening commit. Clear to merge. Cost-ceiling immediately follows as slice 15.
