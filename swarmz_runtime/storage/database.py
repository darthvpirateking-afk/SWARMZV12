# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""SQLAlchemy database engine, session factory, and FastAPI dependency.

Supports PostgreSQL (production) and SQLite (local dev fallback).
Set DATABASE_URL env var to control which backend is used.
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase

logger = logging.getLogger("swarmz.db")

DEFAULT_DATABASE_URL = "sqlite:///./data/swarmz.db"


class Base(DeclarativeBase):
    """ORM base for all SWARMZ models."""
    pass


def _get_database_url() -> str:
    url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    # Railway provides DATABASE_URL with postgres:// but SQLAlchemy 2.0 needs postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def _build_engine(url: str | None = None):
    db_url = url or _get_database_url()
    is_sqlite = db_url.startswith("sqlite")

    connect_args = {"check_same_thread": False} if is_sqlite else {}
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        echo=os.environ.get("SQL_ECHO", "").lower() in ("1", "true"),
    )

    # Enable WAL mode for SQLite (better concurrent reads)
    if is_sqlite:
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, _):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    logger.info("Database engine created: %s", "sqlite" if is_sqlite else "postgresql")
    return engine


# Module-level engine + session factory (lazy init)
_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session.

    Usage:
        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context manager for non-FastAPI code paths (scripts, engines)."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all_tables():
    """Create all tables (for initial setup / dev). Prefer Alembic in production."""
    from swarmz_runtime.storage import orm_models  # noqa: F401 — registers models

    Base.metadata.create_all(bind=get_engine())
    logger.info("All tables created.")


def reset_engine():
    """Reset module-level engine (useful in tests)."""
    global _engine, _SessionLocal
    if _engine:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
