# Roles & Source of Truth

## Source of truth
The Git repo. Nothing counts until merged to `main`.

Contract files:
- `requirements.md`
- `architecture.md`
- `CONVENTIONS.md`
- `AGENTS.md`
- `docs/DECISIONS.md`
- `docs/slices/slice-NN.md`

## Claude
- Spec owner and design reviewer.
- Writes slice specs and proposes design decisions.
- Reviews PRs for spec/design conformance and recommends resolutions to conflicts.
- Does not write production code.
- Does not push.
- Does not run server code.
- Does NOT have final authority — the user approves design decisions.

## Codex
- Implementer.
- Works only from `AGENTS.md` + the active slice spec + `architecture.md` + `CONVENTIONS.md`.
- Creates one branch and one PR per slice.
- Does not change scope.
- Does not edit constitution docs unless the slice explicitly says so.
- Does not read the production `.env` or production DB.
- Runs tests and updates the slice handoff.

## ChatGPT
- Independent QA / research reviewer.
- Reviews PR diffs for bugs, edge cases, security, missing tests, and implementation risk.
- May raise design concerns, but those go through Claude/spec before Codex acts.
- Does not directly command Codex.

## User
- Final decision maker.
- Approves design changes.
- Approves which QA findings become Codex tasks.
- Merges PRs.

## Per-slice loop
1. Claude writes `docs/slices/slice-NN.md` (scope + acceptance criteria). User approves.
2. Codex implements on branch `slice-NN`, runs tests, writes the handoff, opens a PR.
3. ChatGPT reviews the diff for defects.
4. Claude reviews the diff for spec conformance and recommends resolutions.
5. User decides which findings become tasks, approves, and merges to `main`.
6. Every non-trivial decision is logged in `docs/DECISIONS.md`.

## Handoff
Each slice's PR includes a handoff (in the PR description or `docs/slices/slice-NN-handoff.md`):
- What was built.
- Which tests ran and passed.
- Any deviations from the spec.
- Open questions / risks.

## Anti-drift rules
- Design concerns converge into the spec (via Claude) before any code is written — no split-brain.
- Codex obeys only the spec, not whichever AI spoke last.
- Each tool reads the latest repo state before acting; never from memory of an old version.
- One slice per branch; `main` always boots.
