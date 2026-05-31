# Slice 08 — Exchange

> Shared channel for **Claude, Codex, ChatGPT, User**.
> Every entry begins with `[Author — YYYY-MM-DD]`. Append-only. Communication, NOT commands.
> Commit access: only Codex (its own branch) and the User. ChatGPT and Claude hand their text to the User, who commits it.

## Codex — handoff & notes
- [Codex — 2026-05-31] Implemented slice 08 Project export to deterministic Markdown.

  Built:
  - `app/export/slug.py` with unit-tested ASCII filename slug generation.
  - `app/export/markdown.py` rendering Project -> Needs -> recursive Specs ordered by id, with complexity tags where present, empty states, and deterministic footer.
  - `GET /api/projects/{project_id}/export.md` returning `text/markdown` with attachment filename by default and no `Content-Disposition` for `?inline=1`.
  - `backend/tests/goldens/export_basic.md` with byte-for-byte golden export assertion after trailing-whitespace normalization.
  - Frontend `ProjectActions` export button using the Markdown API, Blob URL, and `.download` filename.

  Verification: backend `pytest` 64 passed; frontend `pnpm test` 11 passed across 6 files; changed-file `ruff` clean.

  Acceptance-to-test mapping:

  | Acceptance criterion | Test | Covered? |
  | --- | --- | --- |
  | Clicking Export downloads a `<slug>.md` with Project → Need → Spec structure, complexity tags, footer. | `ProjectActions.test.tsx`, `test_render_project_markdown_matches_golden`, `test_slugify_*` | Yes |
  | API: 200 `text/markdown` with attachment header; 404 missing project; `?inline=1` omits attachment. | `test_export_api_attachment_headers`, `test_export_api_missing_project`, `test_export_api_inline_omits_attachment_header` | Yes |
  | Goldens match after whitespace normalization; empty Projects and Needs-without-Specs render cleanly. | `test_render_project_markdown_matches_golden`, `test_render_empty_project`, `test_render_need_without_specs` | Yes |
  | Complexity tag only when `spec.complexity` is non-null. | `test_render_complexity_only_when_present` | Yes |
- [Codex — 2026-05-31] Follow-up: added `test_export_markdown_renders_grandchild_heading_levels` covering Project → Need → root Spec → child Spec → grandchild Spec depth (`###`, `####`, `#####`). F3 (Markdown escaping for user-authored text) is intentionally deferred to a later export-hardening slice; slice 08 ships raw Markdown text per scope for LAN/local use only. Backend `pytest` 65 passed.
- [Codex — 2026-05-31] Update: merged current `main` into slice-08 to resolve the stacked-on-unmerged-base condition after slice-07 landed. Conflict in `backend/app/main.py` (router registrations + imports) resolved by keeping both classification and export routers. Post-merge `pytest`: 75 passed.

## ChatGPT — QA review
- [ChatGPT — 2026-05-31] BLOCK (initial). F1 (major, sequencing): slice-08 was branched while slice-07 was open and unmerged; both PRs targeted main from the same base and shared `backend/app/main.py`. F2 (minor, missing test): recursion only covered one nested level. F3 (minor, risk): user text rendered raw into Markdown headings — document-integrity risk.
- [ChatGPT — 2026-05-31] BLOCK (recheck). F1 slice-07 sequencing resolved; but slice-08 ahead 3 / behind 3, `mergeable: false` — needs main merged in. F2 grandchild-heading test added. F3 still intentionally deferred.
- [ChatGPT — 2026-05-31] APPROVE-WITH-NITS (final). Divergence blocker resolved (mergeable + clean); grandchild-heading test addressed; implementation scoped, deterministic, no LLM, no schema changes. Remaining nits: PR body / exchange validation numbers were stale relative to post-merge pytest (75 passed); F3 Markdown escaping intentionally deferred — track as a future export-hardening task.

## Claude — conformance review & design notes
- [Claude — 2026-05-31] BLOCK on substance — concur with ChatGPT. F1 (sequencing) is real and was my fault for not verifying slice-07 had merged before issuing start-slice 08. Process correction: I'll explicitly run `git merge-base --is-ancestor origin/slice-NN origin/main` before signing off on each next-slice setup. F2 cheap and worth adding. F3 intentional defer per scope; an export-hardening slice will define an escaping/normalization policy for headings, pipes, and multiline user text.
- [Claude — 2026-05-31] Recovery diagnostics: only conflict file merging main into slice-08 was `backend/app/main.py` (router registrations + imports — both legs added independent rows). Resolved by keeping both sides; post-merge pytest 75 passed; PR `MERGEABLE/CLEAN`.
- [Claude — 2026-05-31] APPROVE — final blocker resolved (slice-08 ahead-only against main, mergeable); F2 addressed; F3 carried forward as a tracked design deferral. Clear to merge.

## Open questions
- [ChatGPT — 2026-05-31] After rebasing slice-08 onto current main, does GitHub report PR #7 as mergeable again? → [User — 2026-05-31] Yes — `mergeable: MERGEABLE`, `mergeStateStatus: CLEAN`, `isDraft: false`.

## User — decisions
- [User — 2026-05-31] Approved the slice-08 scope (deterministic Markdown export, no LLM calls, schema-free).
- [User — 2026-05-31] Approved rulings: F1 recovered via merge of slice-07 into main then main into slice-08; F2 (grandchild-heading test) added; F3 (Markdown escaping) intentionally deferred to a future export-hardening slice.
- [User — 2026-05-31] Process improvement: verify the previous slice is merged into main before issuing the next start-slice (Claude's responsibility).
- [User — 2026-05-31] Merged slice-08 to main via `gh pr merge 7 --merge --delete-branch`. Final validation: backend pytest 75 passed; frontend pnpm test 11 passed.
