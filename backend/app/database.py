"""Database configuration and session management."""
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Get database URL from environment or use default SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./secondbrain.db")

# Create engine
# For SQLite, we need check_same_thread=False to allow usage across threads
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that yields database sessions.

    Usage in FastAPI:
        @app.get("/api/conversations")
        def list_conversations(db: Session = Depends(get_db)):
            return db.query(Conversation).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
