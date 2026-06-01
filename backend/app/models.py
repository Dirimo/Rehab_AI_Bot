"""
Modèles de base de données — SQLModel (compatible SQLite dev / PostgreSQL prod)

► MEMBRE 5 (DevOps / BDD) :
    - Ces 3 tables constituent le schéma complet de l'application.
    - En dev : SQLite est créé automatiquement au démarrage (fichier rehabbot.db).
    - En prod : passer DATABASE_URL=postgresql+asyncpg://... dans .env
    - Si tu ajoutes des colonnes, crée une migration Alembic plutôt que de
      recréer les tables (évite la perte de données en prod).
    - La suppression automatique des sessions expirées est dans database.py → purge_expired_sessions()
      Tu peux l'appeler via un cron ou un script de maintenance.

► MEMBRE 1 (Frontend) :
    - La table `sessions` : id (UUID string), created_at, last_active_at, expires_at, is_active.
      Stocke l'id en localStorage côté client et envoie-le dans chaque requête.
    - La table `messages` : role peut valoir "user", "assistant" ou "tool".
      N'affiche côté chat que role="user" et role="assistant".
"""

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_active_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field()
    is_active: bool = Field(default=True)


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="sessions.id", index=True)
    # Valeurs possibles : "user" | "assistant" | "tool"
    role: str = Field()
    content: str = Field()
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolLog(SQLModel, table=True):
    """
    Trace chaque appel au serveur MCP (Membre 3).
    Utile pour le debug et l'audit de ce que le LLM a demandé.
    """
    __tablename__ = "tool_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="sessions.id", index=True)
    message_id: Optional[int] = Field(default=None, foreign_key="messages.id")
    tool_name: str = Field()
    tool_input: str = Field()   # JSON sérialisé
    tool_output: str = Field()  # JSON sérialisé
    duration_ms: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
