# Slice 08 — Project export to Markdown

Branch: `slice-08` (from `main`). Scope: a deterministic, server-rendered **Markdown export** of a Project's full tree (Needs → Specs, complexity tags where present). No LLM calls; schema-free.

## In scope
1. **Render service** — `app/export/markdown.py`: `render_project_markdown(db, project_id) -> str`. Walks Project → Needs → Specs (ordered by `id` ascending — deterministic). Emits:
   - Project title `# {name}` + optional description (`> {description}` line if present).
   - For each Need: `## Need: {statement}`.
   - For each child Spec under that Need: `### Spec: {statement}` + a complexity tag if classified (`**Complexity:** 3`); deeper recursive child Specs as `#### Spec: ...`, etc.
   - A small footer: `Needs: N`, `Specs: M`, `Classified: X of M`.
   - Empty cases: project with no Needs renders `_No needs yet._` under the title; Need with no Specs renders `_No specs yet._` under its header.
   - No timestamps in the body (keeps tests byte-identical).
2. **API** — `GET /api/projects/{project_id}/export.md` → `text/markdown; charset=utf-8` with `Content-Disposition: attachment; filename="<slug>.md"`. 404 missing project. Query param `?inline=1` returns the same body without the attachment header (for previewing).
3. **Frontend** — an **Export Markdown** button on the Project header (or a small `ProjectActions.tsx`). Click → triggers a browser download of `<slug>.md` via a `Blob` URL. Slugify the filename (lowercase, ASCII-only, non-alphanumerics → hyphens, collapse repeats, trim).
4. **Tests** (deterministic, no LLM calls):
   - Render: build a Project with two Needs, several Specs (some classified, some not, some nested), and assert the output matches a **golden file** in `backend/tests/goldens/export_basic.md` byte-for-byte (after a trailing-whitespace normalize).
   - Render: empty Project renders `_No needs yet._`; Need with no Specs renders `_No specs yet._`.
   - Render: complexity tag appears only when `spec.complexity` is non-null.
   - API: 200 returns correct `Content-Type` + filename header on the attachment; 404 missing project; `?inline=1` omits the attachment header.
   - Frontend: Export button calls the API (mocked), constructs a Blob URL, triggers a download (assert `<a>.download` was set and `click()` invoked); button is disabled when no project is selected.

## Out of scope (build NO behavior)
PDF/HTML export, Mermaid diagrams in the doc, inspector findings (later), cost line in the footer (added when the cost dashboard slice lands), per-prompt-run output, attachments, history/versioning of exports.

## Suggested file layout (one entity/function per file, ≤200 lines)
Backend: `app/export/markdown.py`, `app/export/slug.py`, `app/api/export.py` (register router). Tests: `test_export_markdown.py`, `test_export_api.py`, `test_export_slug.py`. Goldens: `backend/tests/goldens/export_basic.md`.
Frontend: `src/api/export.ts`, `src/components/ProjectActions.tsx`, `ProjectActions.test.tsx`.

## Acceptance criteria
- Clicking Export on a Project downloads a `<slug>.md` file with the Project → Need → Spec structure, complexity tags where classified, and the footer.
- API: 200 `text/markdown` with attachment header; 404 missing project; `?inline=1` omits attachment.
- Goldens match exactly after whitespace normalization; empty Projects and Needs-without-Specs render cleanly.
- `pytest` + `pnpm test` pass. Handoff in `docs/exchange/slice-08.md` with an acceptance-to-test mapping.

## Constraints
- No schema changes, no LLM calls. Determinism is the test discipline: same DB state → byte-identical Markdown. The slug function lives in its own module so it's unit-tested independently. One branch, one PR, no self-merge.
