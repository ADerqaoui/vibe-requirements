"""Migration 0002 tests."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text


def test_migration_0002_round_trips(tmp_path: Path) -> None:
    """Migration 0002 upgrades, downgrades, and upgrades cleanly."""
    database_url = f"sqlite:///{tmp_path / 'migration-store'}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")
    command.downgrade(config, "0001_initial_schema")
    command.upgrade(config, "head")

    engine = create_engine(database_url)
    with engine.connect() as connection:
        table_count = connection.scalar(
            text("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='spec_inspections'")
        )
        index_count = connection.scalar(
            text("SELECT count(*) FROM sqlite_master WHERE type='index' AND name='idx_spec_inspections_spec'")
        )
        columns = connection.execute(text("PRAGMA table_info(spec_inspections)")).all()
        foreign_keys = connection.execute(text("PRAGMA foreign_key_list(spec_inspections)")).all()
    engine.dispose()

    assert table_count == 1
    assert index_count == 1
    assert [column[1] for column in columns] == [
        "id",
        "spec_id",
        "model_id",
        "findings",
        "summary",
        "passes",
        "created_at",
    ]
    assert any(row[2] == "specs" and row[3] == "spec_id" and row[6] == "CASCADE" for row in foreign_keys)
