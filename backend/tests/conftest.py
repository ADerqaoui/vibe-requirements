"""Backend test fixtures."""
import os
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("AUTO_MIGRATE_ON_STARTUP", "false")

from app.db import get_db
from app.main import create_app


@pytest.fixture()
def database_url(tmp_path: Path) -> str:
    """Return a temporary SQLite URL without a forbidden file extension."""
    return f"sqlite:///{tmp_path / 'test-store'}"


@pytest.fixture()
def migrated_database(database_url: str) -> str:
    """Apply Alembic migrations to a temporary database."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    return database_url


@pytest.fixture()
def engine(migrated_database: str) -> Generator[Engine, None, None]:
    """Yield an engine bound to the migrated test database."""
    engine = create_engine(migrated_database, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def configure_connection(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(engine: Engine) -> Generator[Session, None, None]:
    """Yield a direct SQLAlchemy session for assertions and setup."""
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with session_factory() as session:
        yield session


@pytest.fixture()
def api_app(engine: Engine) -> FastAPI:
    """Return a FastAPI app using the migrated test database."""
    app = create_app()
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    async def override_get_db() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    return app
