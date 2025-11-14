"""
PostgreSQL database connection utilities

Provides SQLAlchemy engine and session management.
"""

import logging
import os
from typing import Optional, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

# SQLAlchemy declarative base
Base = declarative_base()

# Global engine and session maker
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def init_postgres(
    database_url: Optional[str] = None,
    pool_size: int = 20,
    max_overflow: int = 0,
    echo: bool = False,
) -> Engine:
    """
    Initialize PostgreSQL connection

    Args:
        database_url: Database URL (defaults to DATABASE_URL env var)
        pool_size: Connection pool size
        max_overflow: Max connections beyond pool_size
        echo: Log all SQL statements

    Returns:
        SQLAlchemy Engine
    """
    global _engine, _SessionLocal

    if _engine is not None:
        logger.warning("PostgreSQL already initialized")
        return _engine

    # Get database URL
    url = database_url or os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL not set")

    # Create engine
    logger.info(f"Initializing PostgreSQL connection: {url.split('@')[1] if '@' in url else 'localhost'}")

    _engine = create_engine(
        url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        echo=echo,
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,   # Recycle connections after 1 hour
    )

    # Create session factory
    _SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine,
    )

    logger.info("PostgreSQL initialized successfully")
    return _engine


def get_postgres_engine() -> Engine:
    """
    Get PostgreSQL engine

    Returns:
        SQLAlchemy Engine

    Raises:
        RuntimeError: If not initialized
    """
    if _engine is None:
        raise RuntimeError("PostgreSQL not initialized. Call init_postgres() first.")
    return _engine


def get_postgres_session() -> Generator[Session, None, None]:
    """
    Get PostgreSQL session (for dependency injection)

    Usage:
        @app.get("/items")
        async def get_items(db: Session = Depends(get_postgres_session)):
            return db.query(Item).all()

    Yields:
        SQLAlchemy Session
    """
    if _SessionLocal is None:
        raise RuntimeError("PostgreSQL not initialized. Call init_postgres() first.")

    db = _SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def postgres_session() -> Generator[Session, None, None]:
    """
    Context manager for PostgreSQL sessions

    Usage:
        with postgres_session() as db:
            user = db.query(User).filter_by(id=user_id).first()

    Yields:
        SQLAlchemy Session
    """
    if _SessionLocal is None:
        raise RuntimeError("PostgreSQL not initialized. Call init_postgres() first.")

    db = _SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def close_postgres():
    """Close PostgreSQL connection"""
    global _engine, _SessionLocal

    if _engine:
        _engine.dispose()
        _engine = None
        _SessionLocal = None
        logger.info("PostgreSQL connection closed")
