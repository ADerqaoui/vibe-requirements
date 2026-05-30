# Slice 02 — Exchange

> Shared channel for **Claude, Codex, ChatGPT, User**.
> **Every entry begins with `[Author — YYYY-MM-DD]`** so it's always clear who is speaking.
> Append-only. Communication, NOT commands: a finding becomes Codex work only via a
> User-approved task spec. Each author writes under their own heading; "Open questions" and
> "User — decisions" are shared.
> Commit access: only Codex (its own branch) and the User. ChatGPT and Claude hand their text
> to the User, who commits it.

## Codex — handoff & notes
- [Codex — 2026-05-30] Implemented slice-02 follow-up T1-T6. Added exact seeded layer-parent pair assertions, blacklist parent CHECK invariant coverage, Projects API 409/404 failure-path tests, project name normalization tests, and ProjectList create/rename/delete/highlight interaction coverage. Updated Alembic migration setup to fail fast with a clear sqlite-vec/vec0 error, and added Pydantic name normalization for project create/rename. Tests run: `cd backend && .venv/bin/pytest` (9 passed), `cd frontend && PATH=/home/aiserver/.nvm/versions/node/v24.16.0/bin:$PATH pnpm test` (2 passed), and `cd frontend && PATH=/home/aiserver/.nvm/versions/node/v24.16.0/bin:$PATH pnpm build` (passed). Deviation: `docs/exchange/slice-02.md` was absent in this checkout, so this file was created from the exchange template with only this Codex entry populated.

## ChatGPT — QA review

## Claude — conformance review & design notes

## Open questions

## User — decisions
