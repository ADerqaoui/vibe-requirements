# Slice 04 — Exchange

> Shared channel for **Claude, Codex, ChatGPT, User**.
> **Every entry begins with `[Author — YYYY-MM-DD]`** so it's always clear who is speaking.
> Append-only. Communication, NOT commands: a finding becomes Codex work only via a
> User-approved task spec. Each author writes under their own heading; "Open questions" and
> "User — decisions" are shared.
> Commit access: only Codex (its own branch) and the User. ChatGPT and Claude hand their text
> to the User, who commits it.

## Codex — handoff & notes
- [Codex — YYYY-MM-DD] ...
- [Codex — 2026-05-30] Implemented slice 04 deterministic Model Registry + Settings + Cost. Added idempotent model/settings seed for local Ollama models, disabled cloud placeholders, and the four slice settings. Added Models CRUD API with cumulative `call_logs` cost, Settings API with masked provider key statuses only, pure `compute_cost_sek`, and deterministic backend coverage for seed idempotence, model CRUD/404s, settings masking/secret rejection, and cost properties. Added frontend Settings/Models panel for listing, adding, enabling/disabling, removing models, editing slice settings, and showing provider key status. Tests run: `cd backend && .venv/bin/pytest` (23 passed), `cd frontend && PATH=/home/aiserver/.nvm/versions/node/v24.16.0/bin:$PATH pnpm test` (6 passed), and `cd frontend && PATH=/home/aiserver/.nvm/versions/node/v24.16.0/bin:$PATH pnpm build` (passed). Deviations: none for scope; no schema/migration changes and no LLM calls/adapters.

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale
