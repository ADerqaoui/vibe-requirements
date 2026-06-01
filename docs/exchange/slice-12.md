# Slice 12 — Exchange

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

[Codex — 2026-06-01] Implemented slice 12 without schema changes. Added a separate `EmbeddingService` for Ollama `/api/embeddings` using the hardcoded `nomic-embed-text` registry tag, retry/timeout behavior matching the chat gateway pattern, and clear missing/disabled model errors. Added parent-scoped `BlacklistService` for transactional rejected-entry + sqlite-vec writes, parent-scoped listing, cosine filtering at hardcoded `0.85`, and generation integration after parsing. Added Need/Spec blacklist API routes and frontend Reject best-effort posting, parent blacklist counter refresh, and the zero-candidate "all blocked" message. `GenerationPanel` was split into small presentational components to keep it at the repo line-count target.

| Acceptance criterion | Test | Covered? |
| --- | --- | --- |
| Rejecting a candidate POSTs to the parent's blacklist endpoint and refreshes the counter. | `frontend/src/components/GenerationPanel.test.tsx` — `generates candidates, accepts one, refetches specs, and rejects one` | Yes |
| Blacklist add persists both `blacklist_entries` and `blacklist_vec` atomically. | `backend/tests/test_blacklist_service.py` — `test_blacklist_add_writes_entry_and_vector`; `backend/tests/test_blacklist_api.py` — `test_blacklist_api_creates_need_and_spec_entries` | Yes |
| Embed failure rolls back the `blacklist_entries` row so no orphan exists. | `backend/tests/test_blacklist_service.py` — `test_blacklist_add_rolls_back_on_embed_failure`; `backend/tests/test_blacklist_api.py` — `test_blacklist_api_errors_and_embed_failure_rolls_back` | Yes |
| Subsequent Generate excludes candidates with cosine >= 0.85 for the same parent. | `backend/tests/test_blacklist_service.py` — `test_filter_against_blacklist_drops_close_candidates`; `backend/tests/test_generation_service.py` — `test_generation_service_filters_parsed_candidates_against_blacklist` | Yes |
| Cross-parent isolation for Need vs Need and Need vs Spec. | `backend/tests/test_blacklist_service.py` — `test_blacklist_list_scopes_by_parent_and_newest_first`; `test_filter_threshold_boundary_and_empty_blacklist`; `backend/tests/test_blacklist_api.py` — `test_blacklist_api_get_returns_newest_first_and_scoped` | Yes |
| Threshold boundary: 0.849 keeps, 0.851 drops; empty blacklist passes through. | `backend/tests/test_blacklist_service.py` — `test_filter_threshold_boundary_and_empty_blacklist` | Yes |
| API: 201 create, 404 missing parent, 422 blank, 502 embed failure with no row, GET scoped + newest-first. | `backend/tests/test_blacklist_api.py` — all tests in file | Yes |
| If filtering drops everything, API returns empty candidates and frontend shows clear empty-state message. | Backend covered by `filter_against_blacklist` empty survivor behavior; frontend covered by `GenerationPanel.test.tsx` — `shows an empty state when all candidates are blocked by the blacklist` | Yes |
| Embedding service parses 768-dim vectors and retries/uses timeout; missing/disabled model gives clear error. | `backend/tests/test_embedding_service.py` — all tests in file | Yes |
| `pytest` + `pnpm test` pass. | `cd backend && .venv/bin/pytest` -> 114 passed; `cd frontend && PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` -> 20 passed | Yes |

Extra validation: `cd frontend && PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm build` passed.

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale

## Claude — final conformance
- [Claude — 2026-06-01] APPROVE — slice scope met; first vector storage in the project is live and exercising sqlite-vec end-to-end. Embedding service correctly factored separately from the chat gateway. Transactional add prevents orphan entries or orphan vectors. Cross-parent isolation enforced. Generation filter integrates without changing the API shape. F1 (slice-11 carryover: classifyingSpecIds not cleared on post-create tree-refresh failure), F2 (frontend test for blacklist-POST failure path), F3 (GenerationPanel.tsx at 241 lines) all minor and grouped together — fold into a single "frontend hygiene" mini-slice when the next UI-heavy slice approaches. DC1 (settings-driven blacklist threshold/embedding model) deferred to the settings slice; will join the classification-tags migration (slice-07 DC2) when settings-driven model selection lands as a coherent unit. Clear to merge.
