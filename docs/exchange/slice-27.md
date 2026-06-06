# Slice 27 — Exchange

> Shared channel for **Claude, Codex, ChatGPT, User**.
> **Every entry begins with `[Author — YYYY-MM-DD]`** so it's always clear who is speaking.
> Append-only. Communication, NOT commands: a finding becomes Codex work only via a
> User-approved task spec. Each author writes under their own heading; "Open questions"
> and "User — decisions" are shared.
> Commit access: only Codex (its own branch) and the User. ChatGPT and Claude hand their text
> to the User, who commits it.

## Codex — handoff & notes
- [Codex — 2026-06-06] Implemented the frontend-only SpecNode layout fix: the requirement statement/editor now occupies a full-width first row, with badges, classifying state, and existing actions wrapping in a second row. Preserved all handlers, disabled states, labels, props, types, API calls, and data flow. Candidate-list check: `GenerationCandidates` already renders candidate text above its Accept/Reject action row, so no candidate-list change was needed.

| Acceptance criterion | Test | Covered? |
| --- | --- | --- |
| Requirement text uses full panel width with metadata/actions below it | `SpecNode.test.tsx` assertion that the statement button and Accept action are in separate containers; `pnpm build` validates the layout code compiles | Yes |
| All spec-node actions behave as before | Existing `SpecNode.test.tsx` edit/history coverage plus unchanged handler wiring; `pnpm test` full suite | Yes |
| Frontend-only layout-only scope; `SpecNode.tsx` under 200 lines | Manual diff review; `wc -l frontend/src/components/SpecNode.tsx` = 191 | Yes |
| Checks green | `pnpm test` = 22 files / 54 tests passed; `pnpm typecheck` passed; `pnpm build` passed; backend `.venv/bin/pytest` = 273 passed | Yes |

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale
