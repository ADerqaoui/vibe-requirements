# Slice 09 — Exchange

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
- [Codex — 2026-05-31] Implemented slice 09 Spec -> child-Spec generation.

  Built:
  - Refactored generation through `generate_for_parent(...)` for Need and Spec parents, with `generate_specs_for_need(...)` preserved as a thin compatibility wrapper.
  - Added `POST /api/specs/{spec_id}/generate`, `POST /api/specs/{spec_id}/specs`, and `GET /api/specs/{spec_id}/specs`.
  - Child Specs persist with `parent_spec_id` set and `status='pending'`; Need Spec listing now returns root Specs only and Spec child listing returns direct children only.
  - Frontend generation now tracks a selected parent (`need` or `spec`), reuses the existing GenerationPanel for Spec parents, and renders Specs recursively with selectable nested nodes.
  - No schema or migration changes.

  Verification:
  - `PYTHONPATH=/tmp/vibe-slice09/backend /home/aiserver/vibe-requirements/backend/.venv/bin/pytest` from `backend/`: 84 passed, 59 warnings.
  - `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` from `frontend/`: 7 files passed, 15 tests passed.
  - `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm exec tsc --noEmit` from `frontend/`: passed.
  - Changed-file backend lint passed. Full `ruff check app tests` still reports pre-existing unused imports in untouched `app/models/blacklist_entry.py` and `app/models/spec_revision.py`.

  Acceptance-to-test mapping:

  | Acceptance criterion | Test | Covered? |
  | --- | --- | --- |
  | Selecting a Spec and generating yields parsed child candidates; Accept creates a child Spec with `parent_spec_id` and `status='pending'`; child appears nested. | `test_spec_generation_api_returns_candidates`, `test_spec_children_api_creates_pending_child`, `GenerationPanel.test.tsx`, `SpecList.test.tsx` | Yes |
  | `POST /api/specs/{id}/generate` and `POST /api/specs/{id}/specs` cover the same status codes as Need-side endpoints. | `test_spec_generation_api_missing_spec_model_disabled_and_count`, `test_spec_generation_api_parser_empty_and_gateway_failure`, `test_spec_children_api_missing_parent_and_blank_statement` | Yes |
  | Need -> Spec generation and slice-06 tests remain compatible. | Existing `test_generations_api.py`, `test_specs_api.py`, `GenerationPanel.test.tsx`; `generate_specs_for_need(...)` wrapper remains. | Yes |
  | Classification and Markdown export continue to work for deeper Specs without schema changes. | Existing `test_classification_api.py`, `test_classification_service.py`, `test_export_markdown.py`, `test_export_api.py` in full pytest run. | Yes |
| Stale candidates clear whenever selected parent changes Need <-> Spec at any depth. | `GenerationPanel.test.tsx` covers Need -> Spec, Spec -> Spec, and Spec -> Need switching. | Yes |
| `pytest` + `pnpm test` pass and handoff includes mapping. | Backend pytest: 84 passed. Frontend pnpm test: 15 passed. This handoff includes the mapping. | Yes |

- [Codex — 2026-05-31] Implemented scoped UX fix so the full Spec tree remains visible while selecting any generation parent.

  Built:
  - Added `GET /api/needs/{need_id}/spec-tree` returning the full nested Spec hierarchy ordered by id, with recursive `children`.
  - Added `parent_spec_id` to `SpecOut` and updated root/child API tests to assert root `null` and child parent ids.
  - Refactored `GenerationPanel` to take `rootNeedId`, fetch `/api/needs/{id}/spec-tree` for display, and keep `selectedParent` independent for Generate/Accept endpoint targeting.
  - Updated recursive `SpecList` usage so selecting root or child Specs changes only selection highlight/target, not the visible tree.
  - On Accept, refetches the root Need spec-tree so accepted children appear nested in place.
  - No schema or migration changes.

  Verification:
  - `.venv/bin/pytest` from `backend/`: 86 passed, 61 warnings.
  - `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` from `frontend/`: 7 files passed, 16 tests passed.
  - `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm exec tsc --noEmit` from `frontend/`: passed.

  Acceptance-to-test mapping:

  | Acceptance criterion | Test | Covered? |
  | --- | --- | --- |
  | `GET /api/needs/{need_id}/spec-tree` returns the Need's full recursive Spec hierarchy ordered by id. | `test_spec_tree_api_returns_recursive_tree` | Yes |
  | Missing Need on spec-tree returns 404. | `test_spec_tree_api_missing_need_returns_404` | Yes |
  | `SpecOut.parent_spec_id` is `null` for root Specs and parent id for children. | `test_specs_api_creates_and_lists_only_need_specs`, `test_spec_children_api_creates_pending_child`, `test_spec_children_api_lists_direct_children_only` | Yes |
  | GenerationPanel fetches full tree once per root Need and keeps tree data independent from selected parent. | `GenerationPanel.test.tsx` integrated tree selection test | Yes |
  | Selecting root and child Specs highlights the selected node without changing tree structure. | `GenerationPanel.test.tsx` integrated tree selection test | Yes |
  | Accept on a child candidate refetches spec-tree and renders the new grandchild nested under the child. | `GenerationPanel.test.tsx` integrated tree selection test | Yes |
  | Stale candidates clear on every parent change. | Existing `GenerationPanel.test.tsx` parent-switch regression test | Yes |
  | Backend pytest and frontend pnpm test pass. | Commands listed above | Yes |

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale

## Claude — final conformance
- [Claude — 2026-05-31] APPROVE — UX fix correctly decouples tree data from selected parent: the recursive /api/needs/{id}/spec-tree endpoint feeds a stable SpecList while selectedParent drives the Generate/Accept target with a visible highlight; Accept refetches the tree so new children appear nested in place. SpecOut now exposes parent_spec_id and status (API observability). Test coverage: integrated nested-rendering + selection-without-data-swap + cross-kind stale-candidate clearing. F2 (stale PR body) housekeeping fixed via gh pr edit. F3 (NeedList lines) deferred — pair with the next UI-heavy slice (inspector) to extract Need row/edit controls. Design baseline going forward: /api/needs/{id}/spec-tree is the canonical tree shape; later slices (inspector, blacklist, export tree views) should reuse it rather than introducing competing tree-state patterns.
