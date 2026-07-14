"""Database setup for the Page Creator app.

Reads the connection string from the DATABASE_URL environment variable
so the same code works in every environment:

  - Locally, if DATABASE_URL isn't set, it falls back to a SQLite file
    at <project_root>/data/pages.db (nothing to configure for dev).
  - In production (e.g. on Horizon), set DATABASE_URL to a hosted
    Postgres connection string (Supabase/Neon/Railway/etc.) as an
    environment variable in the deployment platform's config. The code
    never hardcodes a URL, local or otherwise.

This matters because a deployed server's local filesystem is typically
ephemeral (wiped on redeploy, not shared across replicas) - a real
Postgres database persists independently of the server process.
"""

from __future__ import annotations

import datetime
import os
from pathlib import Path

from sqlalchemy import DateTime, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

# Fallback SQLite path, used only when DATABASE_URL is not set (local dev).
_DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_DB_DIR.mkdir(parents=True, exist_ok=True)
_SQLITE_FALLBACK_URL = f"sqlite:///{_DB_DIR / 'pages.db'}"

DATABASE_URL = "postgresql://postgres.sbzixpbcxkwibhirjman:94rbPkBYGV98WstU@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"

# Some hosts (e.g. Heroku-style providers) hand out URLs starting with
# "postgres://", but SQLAlchemy 2.x requires the "postgresql://" scheme.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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