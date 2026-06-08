"""
Routes REST pour la gestion des sessions — /sessions

► MEMBRE 1 (Frontend / UX) :
    Flux côté client recommandé :
    1. Au chargement de l'app, lire l'id de session dans localStorage ("rehabbot_session_id").
    2. Si absent ou expiré (réponse 410) → POST /sessions pour créer une nouvelle session.
    3. Stocker le nouvel id dans localStorage avec la date d'expiration (expires_at).
    4. Afficher une notification si la session a expiré (GET /sessions/{id} retourne 410).

    Endpoints disponibles :
    POST   /sessions              → crée une session, retourne SessionRead (dont l'id UUID)
    GET    /sessions/{id}         → vérifie si la session est valide (404 = inexistante, 410 = expirée)
    GET    /sessions              → liste toutes les sessions (usage interne / debug)
    DELETE /sessions/{id}         → supprime la session (ex: bouton "Effacer la conversation")

    Format de réponse SessionRead :
    {
      "id": "uuid-string",
      "created_at": "2025-06-01T10:00:00Z",
      "last_active_at": "2025-06-01T10:05:00Z",
      "expires_at": "2025-06-22T10:00:00Z",
      "is_active": true
    }

► MEMBRE 5 (DevOps / BDD) :
    - La durée de vie des sessions est configurée via SESSION_EXPIRY_DAYS dans .env (défaut : 21 jours).
    - La suppression physique est gérée par purge_expired_sessions() dans database.py.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models import Session

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionCreate(BaseModel):
    pass


class SessionRead(BaseModel):
    id: str
    created_at: datetime
    last_active_at: datetime
    expires_at: datetime
    is_active: bool


def _expiry() -> datetime:
    days = int(os.getenv("SESSION_EXPIRY_DAYS", "21"))
    return datetime.now(timezone.utc) + timedelta(days=days)


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(db: AsyncSession = Depends(get_session)):
    session = Session(
        id=str(uuid.uuid4()),
        expires_at=_expiry(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/{session_id}", response_model=SessionRead)
async def get_session_by_id(session_id: str, db: AsyncSession = Depends(get_session)):
    result = await db.exec(select(Session).where(Session.id == session_id))
    session = result.first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")

    now = datetime.now(timezone.utc)
    expires = session.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        session.is_active = False
        await db.commit()
        raise HTTPException(status_code=410, detail="Session expirée")

    return session


@router.get("", response_model=List[SessionRead])
async def list_sessions(db: AsyncSession = Depends(get_session)):
    result = await db.exec(select(Session).order_by(Session.created_at.desc()))
    return result.all()


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_session)):
    result = await db.exec(select(Session).where(Session.id == session_id))
    session = result.first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    await db.delete(session)
    await db.commit()
