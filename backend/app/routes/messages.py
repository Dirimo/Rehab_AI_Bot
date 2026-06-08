"""
Routes REST pour la gestion des messages — /messages

► MEMBRE 1 (Frontend / UX) :
    Ces routes sont utiles pour charger l'historique au démarrage (ex: après un refresh).
    Pour l'envoi de messages en temps réel, utilise le WebSocket /ws/{session_id} à la place.

    Endpoints disponibles :
    POST /messages
        Body : { "session_id": "uuid", "role": "user", "content": "texte" }
        → Ajoute un message à l'historique (sans déclencher le LLM).
        → Retourne le message créé avec son id et created_at.

    GET  /messages/{session_id}
        → Retourne la liste ordonnée (plus ancien en premier) des messages de la session.
        → N'afficher côté UI que role="user" et role="assistant" (ignorer role="tool").
        → Format d'un message :
          {
            "id": 42,
            "session_id": "uuid",
            "role": "user" | "assistant" | "tool",
            "content": "texte",
            "created_at": "2025-06-01T10:05:00Z"
          }

    Codes d'erreur :
        404 → session introuvable
        410 → session expirée (afficher une notification et créer une nouvelle session)

► MEMBRE 5 (DevOps / BDD) :
    - Les messages sont liés à une session via session_id (clé étrangère).
    - La suppression d'une session en cascade supprime ses messages si tu configures
      ondelete="CASCADE" dans Alembic (non activé par défaut avec SQLModel).
"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models import Message, Session

router = APIRouter(prefix="/messages", tags=["messages"])


class MessageCreate(BaseModel):
    session_id: str
    role: str
    content: str


class MessageRead(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    created_at: datetime


async def _assert_session_active(session_id: str, db: AsyncSession) -> Session:
    result = await db.exec(select(Session).where(Session.id == session_id))
    session = result.first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")

    now = datetime.now(timezone.utc)
    expires = session.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        raise HTTPException(status_code=410, detail="Session expirée")

    return session


@router.post("", response_model=MessageRead, status_code=201)
async def create_message(body: MessageCreate, db: AsyncSession = Depends(get_session)):
    session = await _assert_session_active(body.session_id, db)

    message = Message(
        session_id=body.session_id,
        role=body.role,
        content=body.content,
    )
    db.add(message)

    session.last_active_at = datetime.now(timezone.utc)
    db.add(session)

    await db.commit()
    await db.refresh(message)
    return message


@router.get("/{session_id}", response_model=List[MessageRead])
async def get_history(session_id: str, db: AsyncSession = Depends(get_session)):
    await _assert_session_active(session_id, db)
    result = await db.exec(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    return result.all()
