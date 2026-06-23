"""Database engine and session management (async, PostgreSQL via psycopg v3).

We use SQLModel on top of SQLAlchemy's async engine. The flow is:
  - `engine`               : the async connection pool (created once).
  - `async_session_maker`  : factory that produces per-request sessions.
  - `init_db()`            : creates all tables defined by our SQLModel models.
  - `get_session()`        : FastAPI dependency that yields a session and
                             guarantees it is closed afterwards.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings

# `echo=False` keeps logs quiet; flip to True to see every SQL statement.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# expire_on_commit=False lets us keep using objects after commit (handy for
# returning them in API responses without an extra DB round-trip).
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Create database tables for every SQLModel table model.

    Called once on application startup. In production you'd use Alembic
    migrations instead, but create_all is perfect for this project.
    """
    # Importing the models module registers every table=True class with
    # SQLModel.metadata. Without this import, metadata is empty and no tables
    # are created. (noqa: the import is needed for its side effect only.)
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: provide a DB session, then close it automatically."""
    async with async_session_maker() as session:
        yield session
