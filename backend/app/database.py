"""
Configuration de la base de données asynchrone — SQLModel + SQLAlchemy async

► MEMBRE 5 (DevOps / BDD) :
    - Variable DATABASE_URL dans .env (voir .env.example).
      Dev  → sqlite+aiosqlite:///./rehabbot.db  (créé automatiquement, aucune config)
      Prod → postgresql+asyncpg://user:password@host:5432/rehabbot
    - init_db() est appelé au démarrage de l'app (lifespan dans main.py).
      Il crée les tables si elles n'existent pas encore (idempotent).
    - purge_expired_sessions() supprime les sessions dont expires_at est dépassé.
      Appelle cette fonction depuis un script cron quotidien en prod :
        python -c "import asyncio; from app.database import purge_expired_sessions; asyncio.run(purge_expired_sessions())"
    - Pour les migrations (ajout de colonnes), configure Alembic avec le même DATABASE_URL.

► MEMBRE 2 (toi) :
    - get_session() est le dépendance FastAPI injectée dans chaque route REST.
    - AsyncSessionLocal() est utilisé directement dans le WebSocket (pas de Depends disponible).
"""

import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./rehabbot.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


async def purge_expired_sessions() -> int:
    """Supprime les sessions expirées. Retourne le nombre de sessions supprimées."""
    from app.models import Session

    expiry_days = int(os.getenv("SESSION_EXPIRY_DAYS", "21"))
    cutoff = datetime.now(timezone.utc) - timedelta(days=expiry_days)

    async with AsyncSessionLocal() as db:
        result = await db.exec(
            select(Session).where(Session.expires_at < cutoff)
        )
        expired = result.all()
        for s in expired:
            await db.delete(s)
        await db.commit()
        return len(expired)
