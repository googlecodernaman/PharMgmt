"""Database initialization, session management, and migration."""

import logging
from contextlib import contextmanager

from .models import Base, SchemaMeta, engine_factory, session_factory

logger = logging.getLogger("pharmgmt.db")

CURRENT_SCHEMA_VERSION = 2


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


def _migrate_v1_to_v2(db_url: str) -> None:
    """Add bill_type column to parsing_runs table (schema v2)."""
    from sqlalchemy import create_engine, text
    engine = create_engine(db_url)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE parsing_runs ADD COLUMN bill_type VARCHAR"))
            conn.commit()
            logger.info("Migration v1->v2: added bill_type to parsing_runs")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                logger.info("Migration v1->v2: bill_type column already present, skipping")
            else:
                raise
    engine.dispose()


def migrate_db(db_url: str, target_version: int | None = None) -> None:
    """Run database migrations incrementally.

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

    if current < 2:
        _migrate_v1_to_v2(db_url)

    # Update version
    with get_db_session(db_url) as session:
        meta = session.query(SchemaMeta).filter_by(key="schema_version").first()
        if meta:
            meta.value = str(target_version)
        else:
            session.add(SchemaMeta(key="schema_version", value=str(target_version)))

    logger.info("Migration complete — schema version %d", target_version)
