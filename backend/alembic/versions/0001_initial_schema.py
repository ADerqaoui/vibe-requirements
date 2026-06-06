"""Initial schema for slice 02.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-30
"""
from typing import Sequence

from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

BASE_TABLES: Sequence[str] = (
    "settings",
    "call_logs",
    "prompts",
    "models",
    "inspection_findings",
    "spec_revisions",
    "classification_votes",
    "blacklist_entries",
    "diagrams",
    "spec_disciplines",
    "specs",
    "needs",
    "projects",
    "layer_parents",
    "layers",
    "disciplines",
)


def upgrade() -> None:
    """Create every table defined in architecture.md section 2."""
    op.execute("PRAGMA foreign_keys=ON")
    op.execute(
        """
        CREATE TABLE disciplines (
            id          INTEGER PRIMARY KEY,
            name        TEXT NOT NULL UNIQUE
        ) STRICT
        """
    )
    op.execute(
        """
        CREATE TABLE layers (
            id           INTEGER PRIMARY KEY,
            name         TEXT NOT NULL UNIQUE,
            kind         TEXT NOT NULL CHECK (kind IN ('cross_cutting','discipline_locked')),
            discipline   TEXT,
            sort_order   INTEGER NOT NULL
        ) STRICT
        """
    )
    op.execute(
        """
        CREATE TABLE layer_parents (
            layer_id        INTEGER NOT NULL REFERENCES layers(id) ON DELETE CASCADE,
            parent_layer_id INTEGER NOT NULL REFERENCES layers(id) ON DELETE CASCADE,
            PRIMARY KEY (layer_id, parent_layer_id)
        ) STRICT
        """
    )
    op.execute(
        """
        CREATE TABLE projects (
            id          INTEGER PRIMARY KEY,
            name        TEXT NOT NULL UNIQUE,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        ) STRICT
        """
    )
    op.execute(
        """
        CREATE TABLE needs (
            id          INTEGER PRIMARY KEY,
            project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            statement   TEXT NOT NULL,
            context     TEXT,
            constraints TEXT,
            complexity  INTEGER CHECK (complexity BETWEEN 1 AND 5),
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        ) STRICT
        """
    )
    op.execute("CREATE INDEX idx_needs_project ON needs(project_id)")
    op.execute(
        """
        CREATE TABLE specs (
            id             INTEGER PRIMARY KEY,
            need_id        INTEGER NOT NULL REFERENCES needs(id) ON DELETE CASCADE,
            parent_spec_id INTEGER REFERENCES specs(id) ON DELETE CASCADE,
            layer_id       INTEGER NOT NULL REFERENCES layers(id),
            text           TEXT NOT NULL,
            status         TEXT NOT NULL DEFAULT 'pending'
                             CHECK (status IN ('pending','accepted','rejected')),
            source         TEXT NOT NULL DEFAULT 'ai' CHECK (source IN ('ai','manual')),
            complexity     INTEGER CHECK (complexity BETWEEN 1 AND 5),
            gen_model_id   INTEGER REFERENCES models(id),
            gen_prompt_id  INTEGER REFERENCES prompts(id),
            created_at     TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
        ) STRICT
        """
    )
    op.execute("CREATE INDEX idx_specs_need ON specs(need_id)")
    op.execute("CREATE INDEX idx_specs_parent ON specs(parent_spec_id)")
    op.execute(
        """
        CREATE TABLE spec_disciplines (
            spec_id       INTEGER NOT NULL REFERENCES specs(id) ON DELETE CASCADE,
            discipline_id INTEGER NOT NULL REFERENCES disciplines(id),
            PRIMARY KEY (spec_id, discipline_id)
        ) STRICT
        """
    )
    op.execute(
        """
        CREATE TABLE diagrams (
            id             INTEGER PRIMARY KEY,
            spec_id        INTEGER NOT NULL UNIQUE REFERENCES specs(id) ON DELETE CASCADE,
            title          TEXT,
            diagram_type   TEXT NOT NULL,
            mermaid_source TEXT NOT NULL,
            out_of_date    INTEGER NOT NULL DEFAULT 0,
            created_at     TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
        ) STRICT
        """
    )
    op.execute(
        """
        CREATE TABLE blacklist_entries (
            id              INTEGER PRIMARY KEY,
            parent_need_id  INTEGER REFERENCES needs(id) ON DELETE CASCADE,
            parent_spec_id  INTEGER REFERENCES specs(id) ON DELETE CASCADE,
            text            TEXT NOT NULL,
            source          TEXT NOT NULL CHECK (source IN ('rejected','edited_out')),
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            CHECK ( (parent_need_id IS NOT NULL) <> (parent_spec_id IS NOT NULL) )
        ) STRICT
        """
    )
    op.execute("CREATE INDEX idx_blacklist_need ON blacklist_entries(parent_need_id)")
    op.execute("CREATE INDEX idx_blacklist_spec ON blacklist_entries(parent_spec_id)")
    op.execute(
        """
        CREATE VIRTUAL TABLE blacklist_vec USING vec0(
            entry_id INTEGER PRIMARY KEY,
            embedding FLOAT[768]
        )
        """
    )
    op.execute(
        """
        CREATE TABLE classification_votes (
            id           INTEGER PRIMARY KEY,
            parent_type  TEXT NOT NULL CHECK (parent_type IN ('need','spec')),
            parent_id    INTEGER NOT NULL,
            model_id     INTEGER REFERENCES models(id),
            vote         INTEGER CHECK (vote BETWEEN 1 AND 5),
            failed       INTEGER NOT NULL DEFAULT 0,
            created_at   TEXT NOT NULL DEFAULT (datetime('now'))
        ) STRICT
        """
    )
    op.execute("CREATE INDEX idx_votes_parent ON classification_votes(parent_type, parent_id)")
    op.execute(
        """
        CREATE TABLE spec_revisions (
            id           INTEGER PRIMARY KEY,
            spec_id      INTEGER NOT NULL REFERENCES specs(id) ON DELETE CASCADE,
            revision_no  INTEGER NOT NULL,
            text         TEXT NOT NULL,
            layer_id     INTEGER NOT NULL,
            disciplines  TEXT,
            diagram_src  TEXT,
            reason       TEXT,
            archived_at  TEXT NOT NULL DEFAULT (datetime('now'))
        ) STRICT
        """
    )
    op.execute("CREATE INDEX idx_revisions_spec ON spec_revisions(spec_id)")
    op.execute(
        """
        CREATE TABLE inspection_findings (
            id                INTEGER PRIMARY KEY,
            spec_id           INTEGER NOT NULL REFERENCES specs(id) ON DELETE CASCADE,
            spec_revision_id  INTEGER REFERENCES spec_revisions(id),
            category          TEXT NOT NULL,
            severity          TEXT NOT NULL CHECK (severity IN ('critical','major','minor')),
            explanation       TEXT NOT NULL,
            suggested_rewrite TEXT,
            state             TEXT NOT NULL DEFAULT 'open' CHECK (state IN ('open','dismissed')),
            not_evaluated     INTEGER NOT NULL DEFAULT 0,
            inspect_model_id  INTEGER REFERENCES models(id),
            archived_at       TEXT,
            created_at        TEXT NOT NULL DEFAULT (datetime('now'))
        ) STRICT
        """
    )
    op.execute("CREATE INDEX idx_findings_spec ON inspection_findings(spec_id)")
    op.execute(
        """
        CREATE TABLE models (
            id                  INTEGER PRIMARY KEY,
            provider            TEXT NOT NULL,
            name                TEXT NOT NULL,
            ollama_tag          TEXT,
            api_model_id        TEXT,
            tier                TEXT NOT NULL CHECK (tier IN ('low','mid','high')),
            input_cost_per_1k   REAL NOT NULL DEFAULT 0,
            output_cost_per_1k  REAL NOT NULL DEFAULT 0,
            enabled             INTEGER NOT NULL DEFAULT 1,
            created_at          TEXT NOT NULL DEFAULT (datetime('now'))
        ) STRICT
        """
    )
    op.execute(
        """
        CREATE TABLE prompts (
            id               INTEGER PRIMARY KEY,
            name             TEXT NOT NULL,
            description      TEXT,
            layer_id         INTEGER REFERENCES layers(id),
            task             TEXT NOT NULL,
            discipline_scope TEXT,
            version          INTEGER NOT NULL DEFAULT 1,
            template         TEXT NOT NULL,
            enabled          INTEGER NOT NULL DEFAULT 1,
            created_at       TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
        ) STRICT
        """
    )
    op.execute("CREATE INDEX idx_prompts_lookup ON prompts(layer_id, task, discipline_scope, enabled)")
    op.execute(
        """
        CREATE TABLE call_logs (
            id            INTEGER PRIMARY KEY,
            project_id    INTEGER REFERENCES projects(id) ON DELETE SET NULL,
            spec_id       INTEGER REFERENCES specs(id) ON DELETE SET NULL,
            parent_type   TEXT,
            parent_id     INTEGER,
            task          TEXT NOT NULL,
            provider      TEXT NOT NULL,
            model_id      INTEGER REFERENCES models(id),
            prompt_id     INTEGER REFERENCES prompts(id),
            prompt_version INTEGER,
            in_tokens     INTEGER NOT NULL DEFAULT 0,
            out_tokens    INTEGER NOT NULL DEFAULT 0,
            cost_sek      REAL NOT NULL DEFAULT 0,
            fx_rate       REAL NOT NULL DEFAULT 0,
            duration_ms   INTEGER,
            status        TEXT NOT NULL CHECK (status IN ('success','failure')),
            rendered_prompt TEXT,
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        ) STRICT
        """
    )
    op.execute("CREATE INDEX idx_calls_project ON call_logs(project_id)")
    op.execute("CREATE INDEX idx_calls_spec ON call_logs(spec_id)")
    op.execute("CREATE INDEX idx_calls_created ON call_logs(created_at)")
    op.execute(
        """
        CREATE TABLE settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        ) STRICT
        """
    )


def downgrade() -> None:
    """Drop slice 02 schema objects."""
    op.execute("DROP TABLE IF EXISTS blacklist_vec")
    for table_name in BASE_TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table_name}")
