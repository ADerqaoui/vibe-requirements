# Slice 03 — Exchange
> Every entry begins with [Author — YYYY-MM-DD]. Communication, not commands.

## Codex — handoff & notes
- [Codex — 2026-05-30] Implemented slice 03 Needs CRUD on branch slice-03. Backend Need schemas/service/routes: project-scoped list/create, detail, patch (clears complexity, bumps updated_at), delete with DB cascades. Coverage: project scoping, 404s, blank-statement validation, trim/null normalization, complexity cleared on update, missing patch/delete 404s, delete cascading specs + need blacklist rows. Frontend Need type/API/component: selected-project loading, create/edit/delete, confirmation prompt, selected-need highlight, unclassified indicator; lifted selected-project state into App. Tests: backend pytest 14 passed, frontend 4 passed, build passed. Deviation: slice-03 initially pointed at pre-slice-02 main, fast-forwarded to origin/slice-02 before implementing; exchange file was absent so created from template with this entry only.

## ChatGPT — QA review
- [ChatGPT — 2026-05-30] BLOCK (initial + recheck): slice-03 was stacked on unmerged slice-02, so the PR-vs-main diff was inflated (57 files); not isolated to Needs. Required: merge slice-02, rebase slice-03 onto main, re-QA on the clean diff.
- [ChatGPT — 2026-05-30] APPROVE-WITH-NITS (after the git fix): clean Needs-only delta confirmed. Backend CRUD, normalization, cascade, and frontend behaviors all verified. Nits: (minor) no cross-project isolation test; (minor) NeedList.tsx is 253 lines (over the 200 target, under 300). Design concern: NeedList nearing multi-responsibility.

## Claude — conformance review & design notes
- [Claude — 2026-05-30] APPROVE on substance — verified the Needs service + tests independently (project scoping/404, blank→422, complexity cleared + updated_at bumped, spec+blacklist cascade). Concurred with ChatGPT's BLOCK as a git-state issue, not a code defect. Diagnosed: slice-02 never merged + slice-03 stacked on it; fix = merge slice-02, then rebase/fast-forward. Rulings: F2 (cross-project isolation test) deferred — scoping is correct, fold into next needs work; NeedList split (NeedForm/NeedRow/NeedEditor) deferred to the classification/spec slice where the file would actually grow.

## Open questions
- [ChatGPT — 2026-05-30] Should cross-project isolation tests be a required follow-up for slice 03? → [Claude — 2026-05-30] Deferred — not required for this slice; the project_id filter is correct. Add the isolation test next time we touch needs tests.

## User — decisions
- [User — 2026-05-30] Merged slice-03 (Needs CRUD) after both reviews cleared; F2 isolation test deferred, NeedList split deferred to the classification/spec slice.
- [User — 2026-05-30] Adopted the no-stacked-PRs rule: branch each slice from main only after the previous is merged.
