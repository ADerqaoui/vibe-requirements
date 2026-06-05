"""Migration 0003 tests."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text


def test_migration_0003_adds_only_nullable_req_id_column(tmp_path: Path) -> None:
    """Migration 0003 adds the nullable specs.req_id column."""
    database_url = f"sqlite:///{tmp_path / 'migration-store'}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "0002_add_spec_inspections")
    engine = create_engine(database_url)
    with engine.connect() as connection:
        before_columns = connection.execute(text("PRAGMA table_info(specs)")).all()
    engine.dispose()

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    with engine.connect() as connection:
        after_columns = connection.execute(text("PRAGMA table_info(specs)")).all()
    engine.dispose()

    before_names = [column[1] for column in before_columns]
    after_names = [column[1] for column in after_columns]
    req_id_column = next(column for column in after_columns if column[1] == "req_id")

    assert after_names == [*before_names, "req_id"]
    assert req_id_column[2] == "TEXT"
    assert req_id_column[3] == 0
    assert req_id_column[4] is None
