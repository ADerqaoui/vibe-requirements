# Slice 02 — Schema + Reference Seed + Projects CRUD

**Branch:** `slice-02`
**Depends on:** slice-01 (scaffold), `architecture.md` §2 (schema) and §3 (API), `requirements.md` (Section 1 + Section 4), `CONVENTIONS.md`, `AGENTS.md`.

## Objective
Stand up the full database and make Projects fully usable end to end. After this slice, the user can create, list, select, rename, and delete projects backed by real tables, and the reference data (disciplines, layers, V-model parent rules) is seeded.

## In scope
1. **Migration** — one Alembic migration that creates **every table exactly as defined in `architecture.md` §2** (Reference tables, Core hierarchy, Diagrams, Blacklist incl. the `vec0` virtual table, Classification, Revision history & inspector findings, Registries, Call log, Settings). Honor: `STRICT` on all base tables, `PRAGMA foreign_keys=ON` (already in `db.py`), the two-column `blacklist_entries` parent + CHECK, `spec_revisions`, and the `archived_at` / `spec_revision_id` columns on `inspection_findings`.
2. **ORM models** — one SQLAlchemy model per entity, one file each, under `backend/app/models/`. (The `blacklist_vec` virtual table has no ORM model; it is created in the migration and accessed via raw SQL later.)
3. **Reference-data seed** — idempotent, runnable via `python -m app.seed.run`. Seeds exactly the data in the table below. Document the command in `README.md`.
4. **Projects CRUD** — service + API + minimal frontend Projects column that replaces the slice-1 health card.
5. **Tests** — see Acceptance.

## Out of scope (do not build)
Needs, specs, generation, classification, inspector, blacklist logic, router, gateway, prompts behavior, cost, export, diagrams behavior. Their **tables** are created by the migration but get **no** API/UI/logic this slice.

## Reference data to seed

**Disciplines** (3): `SW`, `Electronic`, `Mechanical`.

**Layers** (12): `name | kind | discipline | sort_order`
| name | kind | discipline | sort_order |
|---|---|---|---|
| Need | cross_cutting | (null) | 0 |
| System Requirement | cross_cutting | (null) | 10 |
| System Architecture | cross_cutting | (null) | 20 |
| SW Requirement | discipline_locked | SW | 30 |
| SW Architecture | discipline_locked | SW | 40 |
| SW Component/Unit | discipline_locked | SW | 50 |
| Electronic Requirement | discipline_locked | Electronic | 30 |
| Electronic Architecture | discipline_locked | Electronic | 40 |
| Electronic Component | discipline_locked | Electronic | 50 |
| Mechanical Requirement | discipline_locked | Mechanical | 30 |
| Mechanical Architecture | discipline_locked | Mechanical | 40 |
| Mechanical Component | discipline_locked | Mechanical | 50 |

**Layer parents** (V-model allowed parents; child → [allowed parents]):
- System Requirement → [Need]
- System Architecture → [System Requirement]
- SW Requirement → [System Requirement, System Architecture]
- SW Architecture → [SW Requirement]
- SW Component/Unit → [SW Architecture, SW Requirement]
- Electronic Requirement → [System Requirement, System Architecture]
- Electronic Architecture → [Electronic Requirement]
- Electronic Component → [Electronic Architecture, Electronic Requirement]
- Mechanical Requirement → [System Requirement, System Architecture]
- Mechanical Architecture → [Mechanical Requirement]
- Mechanical Component → [Mechanical Architecture, Mechanical Requirement]
- Need → [] (root, no parents)

Note: `Need` exists as a layer only to anchor the V-model trace. Spec rows never use `layer = Need`; they link to a need via `needs.id`.

## Projects API (per `architecture.md` §3)
FastAPI-idiomatic: return entities directly; errors via HTTP status + `{detail}`.

| Method | Path | Body | Returns | Errors |
|---|---|---|---|---|
| GET | `/api/projects` | — | `[Project]` | — |
| POST | `/api/projects` | `{name}` | `Project` (201) | 409 if name exists (REQ-PROJ-007) |
| GET | `/api/projects/{id}` | — | `Project` (needs `[]` for now) | 404 |
| PATCH | `/api/projects/{id}` | `{name}` | `Project` | 404; 409 on duplicate name |
| DELETE | `/api/projects/{id}` | — | 204 | 404 |

`Project` shape: `{ id, name, created_at }`.

## Suggested file layout (follow CONVENTIONS.md — one function/entity per file)
Backend:
- `app/models/<entity>.py` — one per table (project, need, spec, discipline, layer, layer_parent, spec_discipline, diagram, blacklist_entry, classification_vote, spec_revision, inspection_finding, model, prompt, call_log, setting).
- `alembic/versions/0001_initial_schema.py` — full schema.
- `app/seed/reference_data.py` (the data) + `app/seed/run.py` (idempotent loader, `__main__`).
- `app/schemas/project.py` — `ProjectCreate`, `ProjectRead`, `ProjectRename`.
- `app/services/project_service.py` — create/list/get/rename/delete + duplicate-name guard.
- `app/api/projects.py` — routes; register router in `app/main.py` under `/api`.
- `tests/conftest.py` (test DB fixture), `tests/test_seed.py`, `tests/test_projects.py`.

Frontend:
- `src/types/project.ts` — `Project` type.
- `src/api/projects.ts` — typed fetch wrappers.
- `src/components/ProjectList.tsx` — Projects column (list, create, select+highlight, rename, delete).
- Update `src/App.tsx` to render the Projects column (replace the health card).
- One smoke test (e.g., ProjectList renders + lists from a mocked fetch).

## Acceptance criteria
- `alembic upgrade head` creates every table; `PRAGMA foreign_keys` is ON; base tables are STRICT; `blacklist_vec` virtual table exists.
- `python -m app.seed.run` is idempotent and yields exactly: 3 disciplines, 12 layers, and the layer-parent rows above. Running it twice does not duplicate rows.
- All five Projects endpoints work and persist across restart. Creating a duplicate name returns 409. Deleting a project with (future) children cascades at the DB level.
- Frontend: lists projects, creates one (it appears), renames, deletes; the selected project is visually highlighted.
- `pytest` passes; frontend smoke test passes.
- Handoff written (see `docs/slices/_handoff-template.md`) covering what was built, tests run, deviations, open questions.

## Notes for the implementer (Codex)
- Translate the schema verbatim from `architecture.md` §2 — do not redesign it. If something in the doc looks wrong, stop and note it in the PR; do not silently change it.
- Do not read `.env` or any `*.db`. Use `.env.example` for config shape.
- One branch (`slice-02`), one PR. Do not merge it yourself.
