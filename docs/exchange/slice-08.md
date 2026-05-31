# Slice 08 — Exchange

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
- [Codex — 2026-05-31] Implemented slice 08 Project export to deterministic Markdown.

  Built:
  - `app/export/slug.py` with unit-tested ASCII filename slug generation.
  - `app/export/markdown.py` rendering Project -> Needs -> recursive Specs ordered by id, with complexity tags where present, empty states, and deterministic footer.
  - `GET /api/projects/{project_id}/export.md` returning `text/markdown` with attachment filename by default and no `Content-Disposition` for `?inline=1`.
  - `backend/tests/goldens/export_basic.md` with byte-for-byte golden export assertion after trailing-whitespace normalization.
  - Frontend `ProjectActions` export button using the Markdown API, Blob URL, and `.download` filename.

  Verification:
  - `backend/.venv/bin/pytest` from `backend/`: 64 passed, 44 warnings.
  - `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` from `frontend/`: 6 files passed, 11 tests passed.
  - Changed-file backend lint: `backend/.venv/bin/ruff check app/export app/api/export.py tests/test_export_slug.py tests/test_export_markdown.py tests/test_export_api.py`: passed.

  Acceptance-to-test mapping:

  | Acceptance criterion | Test | Covered? |
  | --- | --- | --- |
  | Clicking Export on a Project downloads a `<slug>.md` file with Project -> Need -> Spec structure, complexity tags, and footer. | `ProjectActions.test.tsx`, `test_render_project_markdown_matches_golden`, `test_slugify_lowercases_and_collapses_separators` | Yes |
  | API: 200 `text/markdown` with attachment header; 404 missing project; `?inline=1` omits attachment. | `test_export_api_attachment_headers`, `test_export_api_missing_project`, `test_export_api_inline_omits_attachment_header` | Yes |
  | Goldens match exactly after whitespace normalization; empty Projects and Needs-without-Specs render cleanly. | `test_render_project_markdown_matches_golden`, `test_render_empty_project`, `test_render_need_without_specs` | Yes |
  | Complexity tag appears only when `spec.complexity` is non-null. | `test_render_complexity_only_when_present` | Yes |
  | `pytest` + `pnpm test` pass; handoff includes acceptance-to-test mapping. | `pytest`: 64 passed. `pnpm test`: 11 passed. This handoff includes the mapping. | Yes |

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale
