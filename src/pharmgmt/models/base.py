"""SQLAlchemy base configuration."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def engine_factory(db_url: str):
    """Create a SQLAlchemy engine with SQLite WAL mode.

    Args:
        db_url: SQLAlchemy database URL (e.g., sqlite:///./pharmgmt.db)

    Returns:
        SQLAlchemy Engine instance
    """
    engine = create_engine(db_url, echo=False)

    # Enable WAL mode for concurrent reads on SQLite
    if "sqlite" in db_url:
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def session_factory(engine):
    """Create a session factory bound to an engine.

    Args:
        engine: SQLAlchemy Engine

    Returns:
        sessionmaker instance
    """
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)
