"""Database setup for the Page Creator app.
...
"""
from __future__ import annotations

import datetime
import os
from pathlib import Path

from sqlalchemy import DateTime, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Fallback SQLite path, used only when DATABASE_URL is not set (local dev).
_DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_DB_DIR.mkdir(parents=True, exist_ok=True)
_SQLITE_FALLBACK_URL = f"sqlite:///{_DB_DIR / 'pages.db'}"

# Read from environment; fall back to local SQLite if not set.
DATABASE_URL = os.environ.get("DATABASE_URL", _SQLITE_FALLBACK_URL)

# Some hosts (e.g. Heroku-style providers) hand out URLs starting with
# "postgres://", but SQLAlchemy 2.x requires the "postgresql://" scheme.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
print(engine,"engine")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
try:
    # Attempt to open a connection and run a simple test query
    with engine.connect() as connection:
        print("✅ Database connection successful!")
except SQLAlchemyError as e:
    print(f"❌ Database connection failed!")
    print(f"Error details: {e}")


class Base(DeclarativeBase):
    pass


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """FastAPI dependency that yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()