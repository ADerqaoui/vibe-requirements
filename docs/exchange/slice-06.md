# Slice 06 — Exchange

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
- [Codex — 2026-05-31] Implemented slice 06 Generation + Accept/Reject for Need-to-Spec using the local gateway path.

  Built:
  - Hardcoded generation prompt in `app/generation/prompts.py`.
  - Permissive parser for numbered, bulleted, bare-line, mixed, and header-skipping model output.
  - Generation service/API for `POST /api/needs/{need_id}/generate` with fake-gateway injection in tests.
  - Specs service/API for `POST /api/needs/{need_id}/specs` and `GET /api/needs/{need_id}/specs`.
  - Frontend generation panel with enabled-model picker, count input, candidate Accept/Reject, and accepted Specs list refresh.

  Verification:
  - `backend/.venv/bin/pytest` from `backend/`: 54 passed, 37 warnings.
  - `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` from `frontend/`: 5 files passed, 8 tests passed.
  - Changed-file backend lint: `backend/.venv/bin/ruff check ...`: passed.

  Acceptance-to-test mapping:

  | Acceptance criterion | Test | Covered? |
  | --- | --- | --- |
  | With an enabled local model selected and a Need chosen, clicking Generate yields N parsed candidate statements; gateway call is logged in `call_logs` with `status='success'`. | `test_generation_api_returns_candidates_and_logs`, `GenerationPanel.test.tsx` | Yes |
  | Accept on a candidate creates a Spec under that Need; the new Spec appears in the Need's Specs list. | `test_specs_api_creates_and_lists_only_need_specs`, `GenerationPanel.test.tsx` | Yes |
  | Reject removes the candidate from the displayed list with no persistence change. | `GenerationPanel.test.tsx` | Yes |
  | `POST /api/needs/{need_id}/generate`: 200 / 404 / 409 / 422 / 502 as specified. | `test_generation_api_returns_candidates_and_logs`, `test_generation_api_missing_need_model_disabled_and_count`, `test_generation_api_parser_empty_and_gateway_failure` | Yes |
  | `POST /api/needs/{need_id}/specs`: 201 / 404 / 422. `GET /api/needs/{need_id}/specs` returns only that Need's specs. | `test_specs_api_creates_and_lists_only_need_specs`, `test_specs_api_missing_need_and_blank_statement` | Yes |
  | Parser handles numbered, bulleted, and bare outputs and skips headers; zero parsed -> clear error. | `test_generation_parser.py` | Yes |
  | `pytest` + `pnpm test` pass; handoff includes acceptance-to-test mapping. | `pytest`: 54 passed. `pnpm test`: 8 passed. This handoff includes the mapping. | Yes |

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale
