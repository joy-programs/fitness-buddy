"""
database.py — SQLAlchemy + SQLite configuration
------------------------------------------------
Creates the async-compatible engine, session factory, and
Base class that all ORM models inherit from.

FastAPI dependency `get_db()` yields a session per request
and closes it cleanly when the request finishes.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLite database file lives in the project root (fitness-buddy/)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fitness_buddy.db")

# connect_args is needed for SQLite to allow multi-threaded access
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,          # set True to log all SQL queries while debugging
)

# Session factory — each request gets its own session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All ORM models inherit from this base class
Base = declarative_base()


def create_all_tables():
    """Create all database tables if they don't already exist."""
    # Import models here so Base is populated before create_all runs
    from backend import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


# ── FastAPI dependency ────────────────────────────────────────
def get_db():
    """
    Yield a SQLAlchemy session for use in a FastAPI route.

    Usage in a route:
        @router.get("/something")
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
