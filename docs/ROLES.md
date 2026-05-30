# Roles & Source of Truth

## Source of truth
The Git repo. Nothing counts until merged to `main`.
Contract files: requirements.md, architecture.md, CONVENTIONS.md, AGENTS.md,
docs/DECISIONS.md, docs/slices/slice-NN.md.

## Claude
- Spec owner and design reviewer. Writes slice specs and proposes design decisions.
- Reviews PRs for spec/design conformance; recommends conflict resolutions.
- Does not write production code. Does not push. Does not run server code.
- Does NOT have final authority — the User approves design decisions.
- No repo write access: hands its text to the User, who commits it.

## Codex
- Implementer. Works only from AGENTS.md + the active slice spec + architecture.md + CONVENTIONS.md.
- One branch + one PR per slice. Commits code + handoff to its own branch (PR-gated).
- Does not change scope. Does not edit constitution docs unless the slice says so.
- Does not read production .env or production DB. Runs tests and writes the handoff.

## ChatGPT
- Independent QA / research reviewer. Reviews PR diffs for bugs, edge cases, security,
  missing tests, implementation risk.
- May raise design concerns, but those go through Claude/spec before Codex acts.
- Does not directly command Codex.
- No repo write access: hands its review text to the User, who commits it.

## User
- Final decision maker. Approves design changes. Approves which QA findings become Codex tasks.
  Merges PRs. The only committer of Claude's and ChatGPT's input.

## Per-slice loop
1. Claude writes docs/slices/slice-NN.md; User approves.
2. Codex implements on slice-NN, writes its handoff in the exchange file, commits, opens a PR.
3. ChatGPT provides its QA review; the User commits it under the ChatGPT heading.
4. Claude provides its conformance review; the User commits it under the Claude heading.
5. User records decisions (exchange file + docs/DECISIONS.md), triages findings into a task
   spec if needed, and merges.

## Exchange channel (cross-agent communication)
All non-code communication lives in docs/exchange/slice-NN.md — one file per slice
(copy docs/exchange/_template.md for a new slice).
- Every entry begins with `[Author — YYYY-MM-DD]` so authorship is always explicit.
- Each author writes under their own heading; "Open questions" and "User — decisions" are shared.
- Communication, NOT commands: a finding becomes Codex work only once the User approves it.
- Commit access: only Codex (its own branch, PR-gated) and the User. ChatGPT and Claude have
  no repo write access — they hand their sections to the User, who commits everything.

## Anti-drift rules
- Design concerns converge into the spec (via Claude, approved by the User) before code is written.
- Codex obeys only the spec, not whichever AI spoke last.
- Each tool reads the latest repo state before acting; never from memory of an old version.
- One slice per branch; `main` always boots.

- No stacked PRs: branch each slice from `main` only after the previous slice is merged.

- No stacked PRs: branch each slice from `main` only after the previous slice is merged.
