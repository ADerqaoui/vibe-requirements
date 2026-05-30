# Slice 03 — Needs CRUD

Branch: `slice-03` (from `main`, after slice-02 is merged).
Scope: Needs CRUD end to end under a selected project. The schema already exists (slice 02).
**No classification logic, no specs, no AI.**

## In scope
1. Backend Needs CRUD, endpoints verbatim from `architecture.md` §3:
   - `GET /api/projects/{project_id}/needs` — list needs in the project (404 if project missing).
   - `POST /api/projects/{project_id}/needs` — create `{statement, context?, constraints?}` (201; 404 if project missing).
   - `GET /api/needs/{id}` — need detail (404). Returns the need's own fields only; specs are a later slice.
   - `PATCH /api/needs/{id}` — edit any of statement/context/constraints; **clears complexity (sets it NULL)** per REQ-NEED-004; bumps `updated_at` (404 if missing).
   - `DELETE /api/needs/{id}` — delete; DB cascade removes descendant specs and the need's blacklist rows (REQ-NEED-009/010) (204; 404 if missing).
2. Validation/normalization (apply the slice-02 convention): `statement` trimmed, reject blank-after-trim (422). `context`/`constraints` trimmed; empty string stored as NULL.
3. ORM: the `Need` model already exists from slice 02 — reuse it. Do NOT change the schema or migration.
4. Frontend Needs column for the selected project:
   - When a project is selected, list its needs (REQ-NEED-006).
   - Create (statement required; context/constraints optional), select + highlight (REQ-NEED-007), edit the three fields (REQ-NEED-002), delete with a confirmation prompt (REQ-NEED-008).
   - Show an "unclassified" indicator on any need whose complexity is null (REQ-NEED-012).
5. Tests: backend + frontend (see Acceptance).

## Out of scope (tables/fields exist; build NO behavior)
Complexity *classification* flow and generation-gating (REQ-NEED-005), specs / spec tree
(`GET /api/needs/{need_id}/specs`), generation, blacklist logic, router, AI.
`complexity` is stored and displayed but never *set* by this slice (stays null until the classification slice).

## API shapes
- `Need`: `{ id, project_id, statement, context, constraints, complexity, created_at, updated_at }` (context/constraints/complexity may be null).
- `NeedCreate`: `{ statement, context?, constraints? }`.
- `NeedUpdate`: `{ statement?, context?, constraints? }` (at least one field present).

## Suggested file layout (mirror Projects; one entity/function per file, ≤200 lines)
Backend: `app/schemas/need.py`, `app/services/need_service.py`, `app/api/needs.py` (register the router), `tests/test_needs.py`.
Frontend: `src/types/need.ts`, `src/api/needs.ts`, `src/components/NeedList.tsx`, wire project-selection → NeedList in `App.tsx`/`ProjectList.tsx`, `NeedList.test.tsx`.

## Acceptance criteria
- List/create are scoped to a project; create under a non-existent project → 404.
- Blank statement → 422; statement is trimmed; empty context/constraints stored as null.
- PATCH updates fields, clears complexity to null, bumps `updated_at`; PATCH/DELETE on a missing id → 404.
- DELETE cascades: with a spec row and a blacklist row inserted under the need (via SQL in the test), deleting the need removes both — proves REQ-NEED-009/010 at the DB level.
- Frontend: selecting a project shows its needs; create/edit/delete/highlight work; delete prompts for confirmation; needs with null complexity show the unclassified indicator.
- `pytest` and `pnpm test` pass.
- Handoff written in `docs/exchange/slice-03.md` under "## Codex — handoff & notes", entry prefixed `[Codex — YYYY-MM-DD]`.

## Constraints
- Do not modify the schema or migration. Do not edit constitution docs. Do not read `.env`.
- One branch, one PR, no self-merge. Build only what is in scope.
