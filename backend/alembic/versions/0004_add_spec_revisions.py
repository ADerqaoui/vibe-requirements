"""Add Spec revision audit trail.

Revision ID: 0004_add_spec_revisions
Revises: 0003_add_spec_req_id
Create Date: 2026-06-06
"""

from alembic import op

revision = "0004_add_spec_revisions"
down_revision = "0003_add_spec_req_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the Spec revision audit table."""
    op.execute("PRAGMA foreign_keys=ON")
    op.execute("DROP INDEX IF EXISTS idx_revisions_spec")
    op.execute("DROP TABLE IF EXISTS spec_revisions")
    op.execute(
        """
        CREATE TABLE spec_revisions (
            id              INTEGER PRIMARY KEY,
            spec_id         INTEGER NOT NULL REFERENCES specs(id) ON DELETE CASCADE,
            revision_number INTEGER NOT NULL,
            text            TEXT NOT NULL,
            status          TEXT NOT NULL,
            source          TEXT NOT NULL,
            change_type     TEXT NOT NULL,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(spec_id, revision_number)
        ) STRICT
        """
    )
    op.execute("CREATE INDEX idx_spec_revisions_spec ON spec_revisions(spec_id)")


def downgrade() -> None:
    """Restore the pre-0004 placeholder revision table."""
    op.execute("DROP INDEX IF EXISTS idx_spec_revisions_spec")
    op.execute("DROP TABLE IF EXISTS spec_revisions")
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
