"""Database initialization, session management, and migration."""

import logging
from contextlib import contextmanager

from .models import Base, SchemaMeta, engine_factory, session_factory

logger = logging.getLogger("pharmgmt.db")

CURRENT_SCHEMA_VERSION = 1


def init_db(db_url: str) -> None:
    """Initialize the database — create all tables and set schema version.

    Args:
        db_url: SQLAlchemy database URL
    """
    engine = engine_factory(db_url)
    Base.metadata.create_all(engine)

    # Insert schema version if not present
    Session = session_factory(engine)
    session = Session()
    try:
        existing = session.query(SchemaMeta).filter_by(key="schema_version").first()
        if not existing:
            session.add(SchemaMeta(key="schema_version", value=str(CURRENT_SCHEMA_VERSION)))
            session.commit()
            logger.info("Database initialized with schema version %d", CURRENT_SCHEMA_VERSION)
        else:
            logger.info("Database already initialized (schema version %s)", existing.value)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


@contextmanager
def get_db_session(db_url: str):
    """Context manager yielding a database session.

    Args:
        db_url: SQLAlchemy database URL

    Yields:
        SQLAlchemy Session
    """
    engine = engine_factory(db_url)
    Session = session_factory(engine)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


def check_schema_version(db_url: str) -> int:
    """Read the schema version from the database.

    Args:
        db_url: SQLAlchemy database URL

    Returns:
        Schema version as integer, or 0 if not set
    """
    with get_db_session(db_url) as session:
        meta = session.query(SchemaMeta).filter_by(key="schema_version").first()
        if meta:
            return int(meta.value)
        return 0


def migrate_db(db_url: str, target_version: int | None = None) -> None:
    """Run database migrations.

    Currently a placeholder — applies schema changes incrementally.

    Args:
        db_url: SQLAlchemy database URL
        target_version: Target schema version (default: latest)
    """
    if target_version is None:
        target_version = CURRENT_SCHEMA_VERSION

    current = check_schema_version(db_url)

    if current >= target_version:
        logger.info("Schema is up to date (version %d)", current)
        return

    logger.info("Migrating from version %d to %d", current, target_version)

    # Future migrations go here as version-specific functions
    # e.g., if current < 2: _migrate_v1_to_v2(db_url)

    # Update version
    with get_db_session(db_url) as session:
        meta = session.query(SchemaMeta).filter_by(key="schema_version").first()
        if meta:
            meta.value = str(target_version)
        else:
            session.add(SchemaMeta(key="schema_version", value=str(target_version)))

    logger.info("Migration complete — schema version %d", target_version)
