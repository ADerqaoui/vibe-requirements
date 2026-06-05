"""Add stable requirement IDs to specs.

Revision ID: 0003_add_spec_req_id
Revises: 0002_add_spec_inspections
Create Date: 2026-06-05
"""

from alembic import op

revision = "0003_add_spec_req_id"
down_revision = "0002_add_spec_inspections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the nullable req_id column only."""
    op.execute("ALTER TABLE specs ADD COLUMN req_id TEXT")


def downgrade() -> None:
    """Remove the req_id column."""
    with op.batch_alter_table("specs") as batch_op:
        batch_op.drop_column("req_id")
