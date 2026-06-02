# Slice 15 — Exchange

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

[Codex — 2026-06-02] Implemented schema-free cost-ceiling enforcement and cost visibility. Paid model calls now pre-check current-month successful `call_logs.cost_sek` against `settings.cost_ceiling_sek` before gateway execution; free models still proceed even when over ceiling. Cost blocks return top-level HTTP 402 bodies with `error: "cost_ceiling_exceeded"`, `spent_sek`, `ceiling_sek`, and `currency: "SEK"`. Added `GET /api/cost-summary`, Settings `CostPanel`, typed frontend cost-ceiling errors, a GenerationPanel ceiling banner, and cost refresh after successful generation. Frontend touched only for the specified cost panel/error surface.

| Acceptance criterion | Test | Covered? |
| --- | --- | --- |
| Setting `cost_ceiling_sek` below current-month spend blocks paid model calls with HTTP 402 + structured body. | `backend/tests/test_gateway_service.py` — `test_service_blocks_paid_model_at_ceiling_before_gateway`; `backend/tests/test_gateway_api.py` — `test_complete_api_cost_ceiling_returns_402_before_gateway`; `backend/tests/test_generations_api.py` — `test_generation_api_cost_ceiling_returns_402`; `backend/tests/test_inspections_api.py` — `test_inspection_api_cost_ceiling_returns_402` | Yes |
| Free local models still complete regardless of spend/ceiling. | `backend/tests/test_gateway_service.py` — `test_service_allows_free_model_even_when_over_ceiling`; `backend/tests/test_gateway_api.py` — `test_complete_api_free_model_ignores_cost_ceiling` | Yes |
| Ceiling `0` blocks paid calls but allows free calls; failed historical calls do not count. | `backend/tests/test_gateway_service.py` — `test_service_zero_ceiling_blocks_paid_but_failed_spend_does_not_count` | Yes |
| Embedding service gates paid models before HTTP attempts. | `backend/tests/test_embedding_service.py` — `test_embedding_service_blocks_paid_embedding_before_http` | Yes |
| Cost panel in Settings shows current-month spend, remaining vs ceiling, all-time spend, and breakdown by provider/model. | `frontend/src/components/CostPanel.test.tsx` — `renders cost summary numbers and breakdowns`; `frontend/src/components/SettingsPanel.test.tsx` — `lists models, settings, and masked key statuses` | Yes |
| Successful generation increments displayed cost without page reload. | `frontend/src/components/CostPanel.test.tsx` — `refetches when refreshSignal changes`; `frontend/src/components/GenerationPanel.test.tsx` — `generates candidates, accepts one, refetches specs, and rejects one` | Yes |
| Generation and auto-classify 402 responses render a non-blocking ceiling banner. | `frontend/src/components/GenerationPanel.test.tsx` — `shows a cost ceiling banner for generation 402 responses`; `shows a cost ceiling banner when auto-classification is blocked` | Yes |
| `GET /api/cost-summary` aggregates current-month/all-time successful paid spend and floors remaining at zero. | `backend/tests/test_cost_service.py` — `test_cost_summary_aggregates_successful_paid_spend`; `backend/tests/test_cost_api.py` — `test_cost_summary_api_returns_documented_shape` | Yes |
| `pytest` + `pnpm test` pass. | `cd backend && .venv/bin/pytest` -> 161 passed; `cd frontend && PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` -> 28 passed | Yes |

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale
