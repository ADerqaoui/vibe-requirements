"""Migration 0004 tests."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

MIGRATION_PATH = Path("alembic/versions/0004_add_spec_revisions.py")


def test_migration_0004_is_clean_create_only() -> None:
    """Migration 0004 upgrade only creates and downgrade only drops."""
    source = MIGRATION_PATH.read_text()
    upgrade_body = source.split("def upgrade() -> None:", maxsplit=1)[1].split(
        "def downgrade() -> None:",
        maxsplit=1,
    )[0]
    downgrade_body = source.split("def downgrade() -> None:", maxsplit=1)[1]

    assert "DROP TABLE" not in upgrade_body
    assert "DROP INDEX" not in upgrade_body
    assert "CREATE TABLE" not in downgrade_body


def test_migration_0004_creates_spec_revisions_table_and_unique_constraint(tmp_path: Path) -> None:
    """Migration 0004 creates the audit table with per-spec revision uniqueness."""
    database_url = f"sqlite:///{tmp_path / 'migration-store'}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    with engine.begin() as connection:
        columns = connection.execute(text("PRAGMA table_info(spec_revisions)")).all()
        indexes = connection.execute(text("PRAGMA index_list(spec_revisions)")).all()
        foreign_keys = connection.execute(text("PRAGMA foreign_key_list(spec_revisions)")).all()
        strict = connection.scalar(
            text("SELECT strict FROM pragma_table_list WHERE name = 'spec_revisions'")
        )
        connection.execute(text("INSERT INTO projects (name) VALUES ('Demo')"))
        connection.execute(text("INSERT INTO needs (project_id, statement) VALUES (1, 'Need')"))
        connection.execute(
            text("INSERT INTO layers (name, kind, sort_order) VALUES ('System Requirement', 'cross_cutting', 10)")
        )
        connection.execute(text("INSERT INTO specs (need_id, layer_id, text) VALUES (1, 1, 'Spec')"))
        connection.execute(
            text(
                """
                INSERT INTO spec_revisions (spec_id, revision_number, text, status, source, change_type)
                VALUES (1, 1, 'Spec', 'pending', 'ai', 'created')
                """
            )
        )
        try:
            connection.execute(
                text(
                    """
                    INSERT INTO spec_revisions (spec_id, revision_number, text, status, source, change_type)
                    VALUES (1, 1, 'Duplicate', 'pending', 'ai', 'created')
                    """
                )
            )
        except IntegrityError:
            duplicate_blocked = True
        else:
            duplicate_blocked = False
    engine.dispose()

    assert [column[1] for column in columns] == [
        "id",
        "spec_id",
        "revision_number",
        "text",
        "status",
        "source",
        "change_type",
        "created_at",
    ]
    assert columns[-1][4] == "datetime('now')"
    assert any(row[1] == "idx_spec_revisions_spec" for row in indexes)
    assert any(row[2] == "specs" and row[3] == "spec_id" and row[6] == "CASCADE" for row in foreign_keys)
    assert strict == 1
    assert duplicate_blocked
