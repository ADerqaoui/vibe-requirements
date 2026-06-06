"""Schema drift guard tests."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.db import Base


def test_migrated_schema_contains_every_metadata_table(tmp_path: Path) -> None:
    """A fresh Alembic upgrade creates every ORM table."""
    _import_all_models()
    database_url = f"sqlite:///{tmp_path / 'schema-drift-store'}"
    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    try:
        actual_tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    expected_tables = set(Base.metadata.tables)
    assert expected_tables <= actual_tables


def _import_all_models() -> None:
    """Populate Base.metadata with every model module."""
    import app.models.blacklist_entry  # noqa: F401
    import app.models.call_log  # noqa: F401
    import app.models.classification_vote  # noqa: F401
    import app.models.diagram  # noqa: F401
    import app.models.discipline  # noqa: F401
    import app.models.inspection_finding  # noqa: F401
    import app.models.layer  # noqa: F401
    import app.models.layer_parent  # noqa: F401
    import app.models.model  # noqa: F401
    import app.models.need  # noqa: F401
    import app.models.project  # noqa: F401
    import app.models.prompt  # noqa: F401
    import app.models.setting  # noqa: F401
    import app.models.spec  # noqa: F401
    import app.models.spec_discipline  # noqa: F401
    import app.models.spec_inspection  # noqa: F401
    import app.models.spec_revision  # noqa: F401
