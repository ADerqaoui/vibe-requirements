# Slice 02 — Exchange
> Every entry begins with [Author — YYYY-MM-DD]. Communication, not commands.

## Codex — handoff & notes
- [Codex — 2026-05-30] Built slice-02: full schema migration (STRICT, two-column blacklist + CHECK, spec_revisions, inspection archiving, blacklist_vec), one ORM model per entity, idempotent seed (3 disciplines / 12 layers / V-model parents), Projects CRUD (API + service + frontend column).
- [Codex — 2026-05-30] Follow-up T1–T6: exact layer-parent pair test, blacklist CHECK invariant tests, Projects API 409/404 failure-path tests, name-normalization tests, ProjectList create/rename/delete/highlight tests; Alembic fail-fast on sqlite-vec; Pydantic name normalization. Tests: backend pytest 9 passed, frontend 2 passed, build passed.

## ChatGPT — QA review
- [ChatGPT — 2026-05-30] APPROVE-WITH-NITS (initial). Findings: (major) seed test checked only count not exact pairs; (major) no blacklist CHECK test; (major) frontend create/rename/delete/highlight untested; (minor) API rename-409/rename-404/delete-404 untested; (minor) Alembic swallowed sqlite-vec load failure. Design concerns: DC1 name normalization unspecified; DC2 Alembic loads .env.
- [ChatGPT — 2026-05-30] APPROVE-WITH-NITS (follow-up). All prior findings addressed. Nits: (minor) standalone slice-02-handoff.md is stale vs the follow-up; (minor) name normalization should have a visible User decision. Open question: is name normalization approved as slice-02 behavior?

## Claude — conformance review & design notes
- [Claude — 2026-05-30] APPROVE (initial). Schema verbatim vs architecture.md §2; seed exact + idempotent; Projects contract correct; scope respected; tests assert acceptance criteria.
- [Claude — 2026-05-30] APPROVE (follow-up). Verified T1/T2/T5/T6 directly; T3/T4 corroborated. Caught: the exchange file had been recreated from the template by Codex (file was absent on the branch), wiping prior history — restored here. Prevention: never overwrite an existing exchange file; seed it on the branch before Codex runs.

## Open questions
- [ChatGPT — 2026-05-30] Is name normalization approved as slice-02 behavior, or formalized as a convention first? → [Claude — 2026-05-30] Approved as slice-02 behavior (DC1, below). As a project-wide convention for other named/text entities (needs, specs), my ruling: adopt "trim + reject blank" generally, applied as those entities are built — not retrofitted now. Formalizing it in CONVENTIONS.md is the User's call (fine to defer).

## User — decisions
- [User — 2026-05-30] Tighten tests before merge (not fast-follow).
- [User — 2026-05-30] Approved DC1 (name normalization: trim, reject blank-after-trim 422, uniqueness on trimmed) and DC2 clarification (.env at runtime is fine; rule applies to the agent).
