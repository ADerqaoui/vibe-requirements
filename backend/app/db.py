"""Database engine, session factory, and per-connection setup."""
import logging

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


@event.listens_for(engine, "connect")
def _configure_connection(dbapi_connection, _connection_record) -> None:
    """Enforce foreign keys and load sqlite-vec on every new connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
    _load_sqlite_vec(dbapi_connection)


def _load_sqlite_vec(dbapi_connection) -> None:
    """Load the sqlite-vec extension; warn (do not crash) if unavailable."""
    try:
        import sqlite_vec

        dbapi_connection.enable_load_extension(True)
        sqlite_vec.load(dbapi_connection)
        dbapi_connection.enable_load_extension(False)
    except Exception as error:  # noqa: BLE001 - boot must not fail on this
        logger.warning("sqlite-vec not loaded (vector features disabled): %s", error)


async def get_db():
    """Yield a database session and ensure it is closed afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
