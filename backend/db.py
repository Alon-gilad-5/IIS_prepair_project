"""Database setup and session management."""

import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session
from backend.models import *  # Import all models for table creation


# Database path: backend/data/app.db by default
DB_DIR = Path(__file__).parent / "data"
DB_DIR.mkdir(exist_ok=True)

DB_PATH = os.getenv("DB_PATH", str(DB_DIR / "app.db"))
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)


def init_db():
    """Initialize database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session (dependency for FastAPI)."""
    with Session(engine) as session:
        yield session
