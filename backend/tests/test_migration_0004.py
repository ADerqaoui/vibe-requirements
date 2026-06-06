from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError


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


def test_migration_0004_replaces_placeholder_columns(tmp_path: Path) -> None:
    """Full upgrade replaces the 0001 placeholder shape with slice-26 columns."""
    database_url = f"sqlite:///{tmp_path / 'migration-store'}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    with engine.connect() as connection:
        column_names = {
            column[1]
            for column in connection.execute(text("PRAGMA table_info(spec_revisions)")).all()
        }
        unique_indexes = [
            row
            for row in connection.execute(text("PRAGMA index_list(spec_revisions)")).all()
            if row[2] == 1
        ]
        unique_index_columns = [
            [
                column[2]
                for column in connection.execute(text(f"PRAGMA index_info({row[1]})")).all()
            ]
            for row in unique_indexes
        ]
    engine.dispose()

    assert {"revision_number", "status", "source", "change_type"} <= column_names
    assert {"revision_no", "disciplines", "diagram_src"}.isdisjoint(column_names)
    assert ["spec_id", "revision_number"] in unique_index_columns


def test_migration_0004_downgrade_then_upgrade_round_trips(tmp_path: Path) -> None:
    """Downgrading 0004 restores the placeholder and upgrading replaces it again."""
    database_url = f"sqlite:///{tmp_path / 'migration-store'}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")
    command.downgrade(config, "0003_add_spec_req_id")
    command.upgrade(config, "head")

    engine = create_engine(database_url)
    with engine.connect() as connection:
        column_names = [
            column[1]
            for column in connection.execute(text("PRAGMA table_info(spec_revisions)")).all()
        ]
    engine.dispose()

    assert "revision_number" in column_names
    assert "revision_no" not in column_names
