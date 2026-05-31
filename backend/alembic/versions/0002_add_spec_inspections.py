"""Add persisted Spec inspections.

Revision ID: 0002_add_spec_inspections
Revises: 0001_initial_schema
Create Date: 2026-05-31
"""

from alembic import op

revision = "0002_add_spec_inspections"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the single-model inspection persistence table."""
    op.execute("PRAGMA foreign_keys=ON")
    op.execute(
        """
        CREATE TABLE spec_inspections (
            id         INTEGER PRIMARY KEY,
            spec_id    INTEGER NOT NULL REFERENCES specs(id) ON DELETE CASCADE,
            model_id   INTEGER NOT NULL REFERENCES models(id),
            findings   TEXT NOT NULL,
            summary    TEXT,
            passes     INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        ) STRICT
        """
    )
    op.execute("CREATE INDEX idx_spec_inspections_spec ON spec_inspections(spec_id)")


def downgrade() -> None:
    """Drop persisted Spec inspections."""
    op.execute("DROP INDEX IF EXISTS idx_spec_inspections_spec")
    op.execute("DROP TABLE IF EXISTS spec_inspections")
