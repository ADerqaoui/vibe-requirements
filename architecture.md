# Architecture — Requirement Review Dashboard

## Document Control

| Field | Value |
|---|---|
| Project | Requirement Review Dashboard |
| Version | v1 — Architecture Baseline |
| Date | 2026-05-29 |
| Companion doc | `requirements.md` (v1 baseline) |
| Stack | React+TS (frontend) · FastAPI/Python (backend) · SQLite + sqlite-vec (DB) · Ollama + cloud LLMs |
| Deployment | Docker Compose on Debian 13 (Ollama runs on host) |

---

## 1. Repository Layout

Monorepo. Backend and frontend live side by side; one `docker-compose.yml` ties them together. Ollama is **not** containerized — it stays on the host with GPU access and is reached over the LAN.

```
reqdash/
├── docker-compose.yml
├── .env.example                 # config template — committed, no secrets
├── .gitignore                   # ignores .venv/, .env, node_modules/, *.db
├── README.md
│
├── backend/
│   ├── pyproject.toml           # deps + tool config (ruff, pytest)
│   ├── .venv/                   # gitignored — created with `python -m venv .venv`
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/            # migration scripts
│   ├── app/
│   │   ├── main.py              # FastAPI app + router mounting + CORS
│   │   ├── config.py            # env/settings loader (pydantic-settings)
│   │   ├── db.py                # engine, session factory, sqlite-vec load
│   │   ├── models/              # SQLAlchemy ORM (one file per entity)
│   │   ├── schemas/             # Pydantic request/response DTOs
│   │   ├── api/                 # route handlers (one file per resource)
│   │   ├── services/            # business logic (router, generation, ...)
│   │   ├── gateway/             # LLM provider adapters + embeddings
│   │   └── seed/                # default prompts, models, layers seed
│   └── tests/                   # pytest (mirrors services + api)
│
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tailwind.config.js
    ├── Dockerfile               # builds static bundle, served by nginx
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api/                 # typed fetch wrappers per resource
        ├── components/          # ProjectList, NeedList, SpecTree, ...
        ├── hooks/               # data-fetching + mutation hooks
        ├── store/               # client state (zustand)
        └── types/               # TS types mirroring backend schemas
```

### Backend module roles

| Folder | Responsibility |
|---|---|
| `api/` | HTTP layer — validate input, call a service, shape the response. No business logic. |
| `services/` | All business logic. `router_service` decides model+prompt; `generation_service`, `classification_service`, `inspector_service` run the AI tasks; `blacklist_service` does embedding + similarity; `prompt_service`, `cost_service`, `export_service` support. |
| `gateway/` | The only code that talks to LLMs. `base.py` defines an abstract `LLMClient`; one adapter per provider. Adding a provider = one new file. |
| `models/` | SQLAlchemy ORM entities. |
| `schemas/` | Pydantic DTOs — the API contract. |
| `seed/` | First-run population of layers, disciplines, default prompts, default models. |

### Frontend component roles

| Component | Responsibility |
|---|---|
| `ProjectList` | Projects column (create/select/rename/delete) |
| `NeedList` | Needs column (flat list, classify indicator) |
| `SpecTree` + `DisciplineBands` | The 3-band (SW/Electronic/Mechanical) spec columns |
| `DescriptionPanel` | Editable text + Mermaid source/render toggle |
| `DiagramView` | `mermaid.js` rendering + error state |
| `InspectorPanel` | Findings list, score, badges, apply/dismiss |
| `RouterControls` | Router ON/OFF, manual model+prompt selectors |
| `CostDashboard` | Today/week/month/all widget + call log |

---

## 2. Database Schema

SQLite. Vector storage for blacklist embeddings via the `sqlite-vec` extension (loaded at connection time in `db.py`). Enums modeled as `TEXT` with `CHECK` constraints. All timestamps `TEXT` (ISO-8601) or `INTEGER` (unix) — shown here as `TEXT`.

**All base (non-virtual) tables are declared `STRICT`** — append `STRICT` after the closing `)` of every `CREATE TABLE`. Virtual tables (`vec0`) are not STRICT. Foreign keys are enforced via `PRAGMA foreign_keys=ON` on every connection (see `db.py`). The DDL blocks below show `STRICT` only on the tables changed in this revision; apply it uniformly to all base tables in the migration.

### Reference tables (seeded)

```sql
CREATE TABLE disciplines (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE          -- 'SW' | 'Electronic' | 'Mechanical'
);

CREATE TABLE layers (
    id           INTEGER PRIMARY KEY,
    name         TEXT NOT NULL UNIQUE,        -- 'System Requirement', 'SW Architecture', ...
    kind         TEXT NOT NULL CHECK (kind IN ('cross_cutting','discipline_locked')),
    discipline   TEXT,                        -- NULL for cross-cutting; else 'SW'|'Electronic'|'Mechanical'
    sort_order   INTEGER NOT NULL             -- V-model depth ordering
);

CREATE TABLE layer_parents (                  -- allowed parent layers (V-model trace)
    layer_id        INTEGER NOT NULL REFERENCES layers(id) ON DELETE CASCADE,
    parent_layer_id INTEGER NOT NULL REFERENCES layers(id) ON DELETE CASCADE,
    PRIMARY KEY (layer_id, parent_layer_id)
);
```

### Core hierarchy

```sql
CREATE TABLE projects (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE needs (
    id          INTEGER PRIMARY KEY,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    statement   TEXT NOT NULL,
    context     TEXT,
    constraints TEXT,
    complexity  INTEGER CHECK (complexity BETWEEN 1 AND 5),   -- NULL = unclassified
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_needs_project ON needs(project_id);

CREATE TABLE specs (
    id             INTEGER PRIMARY KEY,
    need_id        INTEGER NOT NULL REFERENCES needs(id) ON DELETE CASCADE,
    parent_spec_id INTEGER REFERENCES specs(id) ON DELETE CASCADE,  -- NULL = top-level under Need
    layer_id       INTEGER NOT NULL REFERENCES layers(id),
    text           TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending','accepted','rejected')),
    source         TEXT NOT NULL DEFAULT 'ai' CHECK (source IN ('ai','manual')),
    complexity     INTEGER CHECK (complexity BETWEEN 1 AND 5),      -- NULL = unclassified
    gen_model_id   INTEGER REFERENCES models(id),                   -- which model produced it
    gen_prompt_id  INTEGER REFERENCES prompts(id),                  -- which prompt (id+version)
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_specs_need   ON specs(need_id);
CREATE INDEX idx_specs_parent ON specs(parent_spec_id);

CREATE TABLE spec_disciplines (               -- a spec's discipline set (1-3 rows)
    spec_id       INTEGER NOT NULL REFERENCES specs(id) ON DELETE CASCADE,
    discipline_id INTEGER NOT NULL REFERENCES disciplines(id),
    PRIMARY KEY (spec_id, discipline_id)
);
```

### Diagrams

```sql
CREATE TABLE diagrams (
    id             INTEGER PRIMARY KEY,
    spec_id        INTEGER NOT NULL UNIQUE REFERENCES specs(id) ON DELETE CASCADE,
    title          TEXT,
    diagram_type   TEXT NOT NULL,             -- 'flowchart'|'sequence'|'state'|'class'|'er'|'block'
    mermaid_source TEXT NOT NULL,
    out_of_date    INTEGER NOT NULL DEFAULT 0,-- flag set when spec text edited
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### Blacklist (text + vector)

```sql
CREATE TABLE blacklist_entries (
    id              INTEGER PRIMARY KEY,
    parent_need_id  INTEGER REFERENCES needs(id) ON DELETE CASCADE,   -- nullable
    parent_spec_id  INTEGER REFERENCES specs(id) ON DELETE CASCADE,   -- nullable
    text            TEXT NOT NULL,
    source          TEXT NOT NULL CHECK (source IN ('rejected','edited_out')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    -- exactly one parent must be set (DB-enforced, not service-layer)
    CHECK ( (parent_need_id IS NOT NULL) <> (parent_spec_id IS NOT NULL) )
) STRICT;
CREATE INDEX idx_blacklist_need ON blacklist_entries(parent_need_id);
CREATE INDEX idx_blacklist_spec ON blacklist_entries(parent_spec_id);

-- sqlite-vec virtual table: embedding keyed by blacklist_entries.id
CREATE VIRTUAL TABLE blacklist_vec USING vec0(
    entry_id INTEGER PRIMARY KEY,
    embedding FLOAT[768]                       -- nomic-embed-text dimension
);
```

### Classification (votes + final)

Final value lives on `needs.complexity` / `specs.complexity`. Individual model votes are kept for audit.

```sql
CREATE TABLE classification_votes (
    id           INTEGER PRIMARY KEY,
    parent_type  TEXT NOT NULL CHECK (parent_type IN ('need','spec')),
    parent_id    INTEGER NOT NULL,
    model_id     INTEGER REFERENCES models(id),
    vote         INTEGER CHECK (vote BETWEEN 1 AND 5),  -- NULL if that model failed
    failed       INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_votes_parent ON classification_votes(parent_type, parent_id);
```

### Revision history & inspector findings

Editing an accepted spec preserves the prior version in `spec_revisions` (read-only history). Inspection findings are **archived** (not deleted) when a spec is accepted, so review evidence is retained.

```sql
CREATE TABLE spec_revisions (
    id           INTEGER PRIMARY KEY,
    spec_id      INTEGER NOT NULL REFERENCES specs(id) ON DELETE CASCADE,
    revision_no  INTEGER NOT NULL,            -- 1,2,3… per spec
    text         TEXT NOT NULL,               -- the superseded text
    layer_id     INTEGER NOT NULL,            -- snapshot
    disciplines  TEXT,                        -- snapshot (comma-separated)
    diagram_src  TEXT,                        -- snapshot of mermaid source, nullable
    reason       TEXT,                        -- e.g. 'edited'
    archived_at  TEXT NOT NULL DEFAULT (datetime('now'))
) STRICT;
CREATE INDEX idx_revisions_spec ON spec_revisions(spec_id);

CREATE TABLE inspection_findings (
    id                INTEGER PRIMARY KEY,
    spec_id           INTEGER NOT NULL REFERENCES specs(id) ON DELETE CASCADE,
    spec_revision_id  INTEGER REFERENCES spec_revisions(id),  -- nullable; version the finding judged
    category          TEXT NOT NULL,          -- 'ambiguity'|'verifiability'|... |'diagram_syntax'|...
    severity          TEXT NOT NULL CHECK (severity IN ('critical','major','minor')),
    explanation       TEXT NOT NULL,
    suggested_rewrite TEXT,
    state             TEXT NOT NULL DEFAULT 'open' CHECK (state IN ('open','dismissed')),
    not_evaluated     INTEGER NOT NULL DEFAULT 0,  -- set when call/retry limit hit
    inspect_model_id  INTEGER REFERENCES models(id),
    archived_at       TEXT,                   -- nullable; set on accept instead of deleting
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
) STRICT;
CREATE INDEX idx_findings_spec ON inspection_findings(spec_id);
```

### Registries

```sql
CREATE TABLE models (
    id                  INTEGER PRIMARY KEY,
    provider            TEXT NOT NULL,        -- 'ollama'|'anthropic'|'openai'|'deepseek'
    name                TEXT NOT NULL,        -- display name
    ollama_tag          TEXT,                 -- e.g. 'qwen2.5:7b-instruct' (local only)
    api_model_id        TEXT,                 -- e.g. 'claude-opus-4-8' (cloud only)
    tier                TEXT NOT NULL CHECK (tier IN ('low','mid','high')),
    input_cost_per_1k   REAL NOT NULL DEFAULT 0,   -- USD per 1k input tokens
    output_cost_per_1k  REAL NOT NULL DEFAULT 0,   -- USD per 1k output tokens
    enabled             INTEGER NOT NULL DEFAULT 1,
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE prompts (
    id               INTEGER PRIMARY KEY,
    name             TEXT NOT NULL,
    description      TEXT,
    layer_id         INTEGER REFERENCES layers(id),     -- NULL for layer-agnostic tasks (inspect, classify)
    task             TEXT NOT NULL,           -- see REQ-PROMPT-003 (14 task types)
    discipline_scope TEXT,                    -- NULL | 'SW'|'Electronic'|'Mechanical' | 'any'
    version          INTEGER NOT NULL DEFAULT 1,
    template         TEXT NOT NULL,
    enabled          INTEGER NOT NULL DEFAULT 1,
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_prompts_lookup ON prompts(layer_id, task, discipline_scope, enabled);
-- Invariant (enforced in service layer): at most one enabled prompt per (layer_id, task, discipline_scope).
```

### Call log (cost + audit)

```sql
CREATE TABLE call_logs (
    id            INTEGER PRIMARY KEY,
    project_id    INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    spec_id       INTEGER REFERENCES specs(id) ON DELETE SET NULL,
    parent_type   TEXT,                       -- 'need'|'spec' (what the call was about)
    parent_id     INTEGER,
    task          TEXT NOT NULL,
    provider      TEXT NOT NULL,
    model_id      INTEGER REFERENCES models(id),
    prompt_id     INTEGER REFERENCES prompts(id),
    prompt_version INTEGER,
    in_tokens     INTEGER NOT NULL DEFAULT 0,
    out_tokens    INTEGER NOT NULL DEFAULT 0,
    cost_sek      REAL NOT NULL DEFAULT 0,    -- frozen at call time
    fx_rate       REAL NOT NULL DEFAULT 0,    -- USD->SEK applied (frozen)
    duration_ms   INTEGER,
    status        TEXT NOT NULL CHECK (status IN ('success','failure')),
    rendered_prompt TEXT,                     -- for "view last sent prompt"
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_calls_project ON call_logs(project_id);
CREATE INDEX idx_calls_spec    ON call_logs(spec_id);
CREATE INDEX idx_calls_created ON call_logs(created_at);
```

### Settings (key-value)

```sql
CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
-- Seeded keys: usd_sek_rate, ceiling_default_sek, embedding_model,
--   classifier_model_1/2/3, similarity_threshold, gen_retry_count,
--   inspect_max_calls, inspect_retry_count, call_timeout_cloud_s,
--   call_timeout_local_s, ollama_host, log_level, router_mode
-- NOTE: API keys are NOT stored here. They live in .env (env vars) only,
--   and never enter the DB or any backup dump.
```

### Schema notes

- The `specs` self-reference (`parent_spec_id`) is the V-model tree of arbitrary depth.
- `spec_disciplines` is the discipline set; multi-discipline specs have multiple rows here and render in multiple bands (same node).
- `blacklist_entries` uses two nullable FK columns (`parent_need_id`, `parent_spec_id`) with a CHECK that exactly one is set — DB-enforced, with real `ON DELETE CASCADE`. (Note: `classification_votes` is still polymorphic via `parent_type/parent_id`; left as-is for v1 — fix later if it matters.)
- `ON DELETE CASCADE` on `needs`, `specs`, `diagrams`, `spec_disciplines`, `spec_revisions`, `inspection_findings`, and both blacklist parent FKs implements the cascade-delete rules at the DB level.
- Revision history: editing an accepted spec snapshots the old version into `spec_revisions` (read-only). Inspection findings are archived (`archived_at` set), not deleted, on accept — review evidence is preserved.
- API keys live in `.env` (environment variables) only — never in the DB or backups. The Settings UI shows configured/not-configured status (masked); changing a key means editing `.env` and restarting.

---

## 3. API Surface

REST over JSON. Base path `/api`. All list endpoints return arrays; all mutations return the updated entity. Errors use standard HTTP codes with a `{detail}` body.

### Projects

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/projects` | List projects |
| POST | `/api/projects` | Create `{name}` |
| GET | `/api/projects/{id}` | Project + its needs |
| PATCH | `/api/projects/{id}` | Rename `{name}` |
| DELETE | `/api/projects/{id}` | Delete (cascade) |
| GET | `/api/projects/{id}/export` | MD export — query: `status`, `disciplines`, `findings`, `need_id?` |

### Needs

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/projects/{project_id}/needs` | List needs |
| POST | `/api/projects/{project_id}/needs` | Create `{statement, context?, constraints?}` |
| GET | `/api/needs/{id}` | Need detail |
| PATCH | `/api/needs/{id}` | Edit fields → clears classification |
| DELETE | `/api/needs/{id}` | Delete (cascade specs + blacklist) |

### Specs

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/needs/{need_id}/specs` | Full spec tree under a need |
| GET | `/api/specs/{id}` | Spec detail (+ diagram, findings) |
| POST | `/api/specs` | Manual create `{need_id, parent_spec_id?, layer_id, disciplines[], text}` |
| PATCH | `/api/specs/{id}` | Edit text → cascade rules (REQ-GEN-017/018) |
| DELETE | `/api/specs/{id}` | Delete (cascade) |
| POST | `/api/specs/{id}/accept` | Set status accepted |
| POST | `/api/specs/{id}/reject` | Set status rejected (greyed until next generate) |

### Generation

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/generate` | `{parent_type, parent_id, layer_id, disciplines[], n?, ceiling_ack?}` → blacklists rejected, routes, generates, similarity-filters, returns Pending candidates |

### Classification

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/classify` | `{parent_type, parent_id}` → runs 3 local models, returns votes |
| PUT | `/api/classify` | `{parent_type, parent_id, final}` → confirm/override final value |

### Inspection

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/specs/{id}/inspect` | `{ceiling_ack?}` → multi-pass, returns findings + score |
| GET | `/api/specs/{id}/findings` | Current findings |
| POST | `/api/findings/{id}/apply` | Apply suggested rewrite (= edit) |
| POST | `/api/findings/{id}/dismiss` | Dismiss finding |

### Diagrams

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/specs/{id}/diagram` | Add manual diagram `{diagram_type}` → generates |
| PATCH | `/api/specs/{id}/diagram` | Edit mermaid source (validated) |
| POST | `/api/specs/{id}/diagram/regenerate` | AI redo, text unchanged |

### Blacklist

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/blacklist` | Query `?parent_type=&parent_id=` |
| DELETE | `/api/blacklist/{id}` | Remove entry (un-blacklist) |

### Prompts

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/prompts` | List, filter `?layer_id=&task=&discipline=&enabled=` |
| POST | `/api/prompts` | Create |
| GET | `/api/prompts/{id}` | Detail |
| PUT | `/api/prompts/{id}` | Edit → new version, old disabled |
| POST | `/api/prompts/{id}/enable` | Enable (disables others in tuple) |
| POST | `/api/prompts/{id}/disable` | Disable |
| POST | `/api/prompts/{id}/preview` | Render with sample inputs (no LLM) |
| POST | `/api/prompts/{id}/test` | Run once via router (costs tokens) |

### Models

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/models` | List + cumulative cost |
| POST | `/api/models` | Add |
| PATCH | `/api/models/{id}` | Edit / enable / disable |
| DELETE | `/api/models/{id}` | Remove |

### Router & Settings

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/router` | Current mode + manual selection state |
| PUT | `/api/router` | `{mode: 'on'\|'off', model_id?, prompt_id?}` |
| GET | `/api/settings` | All settings (keys masked) |
| PUT | `/api/settings` | Update settings |
| GET | `/api/layers` | Seeded layers + parent rules |
| GET | `/api/disciplines` | Seeded disciplines |

### Cost

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/cost/summary` | Dashboard totals: today / week / month / all |
| GET | `/api/cost/calls` | Call log, filterable |
| GET | `/api/cost/calls/export` | CSV download |

### Backup

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/backup` | Download full DB dump |
| POST | `/api/restore` | Upload + replace (after confirmation) |

### Cross-cutting patterns

- **Cost ceiling** (REQ-COST-011): `/api/generate`, `/api/inspect`, and `/api/prompts/{id}/test` check the project ceiling first. If exceeded, they return `409 Conflict` with `{ceiling: true, current, ceiling, project_id}`. The client shows the modal; on "allow" it re-sends with `ceiling_ack: true`; on "raise" it `PUT /api/settings` then retries.
- **Async + progress** (REQ-NFR-013/14): long endpoints (generate, classify, inspect) run async; the UI shows a progress indicator and stays responsive. Streaming (REQ-NFR-016) is deferred to v2.
- **Concurrency** (REQ-NFR-015): cloud calls run in parallel; Ollama calls are serialized through a single in-process queue in the gateway.
- **Audit**: every LLM call writes a `call_logs` row including the rendered prompt, enabling "view last sent prompt".

---

## 4. Build Order (preview)

When we move to coding, vertical slices in this order keep each step testable end-to-end:

1. Scaffold: repo, venv, FastAPI skeleton, SQLite + Alembic, React+Vite, Docker Compose.
2. Reference data: layers, disciplines, models, default prompts seed.
3. Projects → Needs CRUD (no AI yet) — proves the full stack works.
4. Gateway + Router (manual mode first) — one real LLM call end-to-end.
5. Generation + Accept/Reject.
6. Classification (3-model vote).
7. Blacklist (embeddings + similarity + retry).
8. Inspector (multi-pass + second opinion).
9. Diagrams (generate + render + edit).
10. Cost tracking + ceiling.
11. Export (MD).
12. Router ON (auto mode) + Settings polish.

---

*End of architecture document.*
