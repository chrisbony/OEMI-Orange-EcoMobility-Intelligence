"""
backend/app/db/session.py
SQLAlchemy 2.0 Engine and SessionLocal configuration for Neon Cloud PostgreSQL/PostGIS.
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Engine with pool_pre_ping and recycle to handle Neon serverless compute sleep
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=False,
    connect_args={
        "sslmode": "require",
    }
)

# Thread-safe session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency providing a transactional DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
