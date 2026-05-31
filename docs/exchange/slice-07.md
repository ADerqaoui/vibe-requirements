# Slice 07 — Exchange

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
- [Codex — 2026-05-31] Implemented slice 07 Classification for Specs via three enabled local Ollama model votes.

  Built:
  - Hardcoded complexity prompt in `app/classification/prompts.py`.
  - Vote parser extracting the first valid 1-5 digit with clear parse errors.
  - Classification service that pre-validates required enabled model tags (`qwen2.5:7b`, `llama3.1:8b`, `gemma2:9b`), calls the slice-05 gateway service through `asyncio.gather`, parses votes, persists the median to `specs.complexity`, and leaves complexity unchanged on gateway failure.
  - `POST /api/specs/{spec_id}/classify` with 404 / 409 / 502 behavior.
  - Frontend SpecList Classify button, loading state, complexity badge, and per-model vote tooltip.

  Verification:
  - `backend/.venv/bin/pytest` from `backend/`: 64 passed, 42 warnings.
  - `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` from `frontend/`: 6 files passed, 10 tests passed.
  - Changed-file backend lint: `backend/.venv/bin/ruff check ...`: passed.

  Acceptance-to-test mapping:

  | Acceptance criterion | Test | Covered? |
  | --- | --- | --- |
  | Clicking Classify on a Spec calls three local models in parallel, parses three votes, persists the median in `specs.complexity`, and writes three success `call_logs`. | `test_classification_service_persists_median_and_logs`, `test_classification_api_returns_votes_and_complexity`, `SpecList.test.tsx` | Yes |
  | Missing/disabled required classification model returns 409 with a clear message and makes no gateway calls. | `test_classification_service_missing_model_prevents_gateway_calls`, `test_classification_api_missing_spec_and_model_conflict` | Yes |
  | Any gateway failure returns 502 with no partial-vote tolerance. | `test_classification_api_gateway_failure_returns_502` | Yes |
  | Complexity badge appears on the Spec and tooltip shows per-model votes. | `SpecList.test.tsx` | Yes |
  | `pytest` + `pnpm test` pass; handoff includes acceptance-to-test mapping. | `pytest`: 64 passed. `pnpm test`: 10 passed. This handoff includes the mapping. | Yes |

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale
