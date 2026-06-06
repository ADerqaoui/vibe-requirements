"""Startup database setup."""
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.config import Settings
from app.seed import run as seed_run


def run_startup_db_setup(settings: Settings) -> None:
    """Apply migrations and seed reference data before the app serves traffic."""
    if not settings.auto_migrate_on_startup:
        return

    try:
        alembic_config = _build_alembic_config(settings)
        command.upgrade(alembic_config, "head")
        seed_run.main()
    except Exception:
        logging.exception("Startup database setup failed")
        raise


def _build_alembic_config(settings: Settings) -> Config:
    """Build an Alembic config with paths independent of the process cwd."""
    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    return config
