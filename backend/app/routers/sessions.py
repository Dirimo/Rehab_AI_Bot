"""Session routes: create, fetch, and delete conversations.

These endpoints are what Member 1 (Frontend) will call to:
  - start a new chat (POST /sessions)
  - resume an existing chat (GET /sessions/{id})
  - clear a conversation (DELETE /sessions/{id})
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.database import get_session
from app.models import Message, Session as ChatSession, ToolLog
from app.schemas import SessionRead

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _to_read(chat_session: ChatSession) -> SessionRead:
    """Convert a DB row into the public API response, with expiry computed."""
    now = datetime.now(timezone.utc)
    expires_at = chat_session.expires_at
    # PostgreSQL may return naive datetimes; treat them as UTC for comparison.
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return SessionRead(
        id=chat_session.id,
        created_at=chat_session.created_at,
        expires_at=chat_session.expires_at,
        is_expired=now > expires_at,
    )


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(
    db: AsyncSession = Depends(get_session),
) -> SessionRead:
    """Create a new conversation and return its id for the browser to store."""
    now = datetime.now(timezone.utc)
    chat_session = ChatSession(
        expires_at=now + timedelta(days=settings.SESSION_EXPIRATION_DAYS),
    )
    db.add(chat_session)
    await db.commit()
    await db.refresh(chat_session)
    return _to_read(chat_session)


@router.get("/{session_id}", response_model=SessionRead)
async def get_session_by_id(
    session_id: str,
    db: AsyncSession = Depends(get_session),
) -> SessionRead:
    """Fetch one session. Returns 404 if the id does not exist."""
    chat_session = await db.get(ChatSession, session_id)
    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return _to_read(chat_session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_session),
) -> None:
    """Delete a session and all its messages and tool logs."""
    chat_session = await db.get(ChatSession, session_id)
    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Child rows reference sessions.id — delete them first (no CASCADE yet).
    await db.execute(delete(Message).where(Message.session_id == session_id))
    await db.execute(delete(ToolLog).where(ToolLog.session_id == session_id))
    await db.delete(chat_session)
    await db.commit()
