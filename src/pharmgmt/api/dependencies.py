"""FastAPI dependencies for dependency injection."""

from pharmgmt.config import get_settings
from pharmgmt.models import engine_factory, session_factory


def get_db():
    """Yield a database session for request handling."""
    settings = get_settings()
    engine = engine_factory(settings.DATABASE_URL)
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
