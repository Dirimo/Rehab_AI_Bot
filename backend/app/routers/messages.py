"""Message routes: send and fetch conversation history.

Member 1 (Frontend) uses these to display chat history.
Member 2 (Agent loop, later) will also write assistant/tool messages here.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models import Message, Session as ChatSession
from app.schemas import MessageCreate, MessageRead

router = APIRouter(prefix="/messages", tags=["messages"])


def _is_expired(chat_session: ChatSession) -> bool:
    """True if the session is past its expires_at timestamp."""
    now = datetime.now(timezone.utc)
    expires_at = chat_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return now > expires_at


async def _get_session_or_404(
    session_id: str,
    db: AsyncSession,
) -> ChatSession:
    chat_session = await db.get(ChatSession, session_id)
    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return chat_session


@router.post("", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def create_message(
    payload: MessageCreate,
    db: AsyncSession = Depends(get_session),
) -> MessageRead:
    """Store one message in a session. Rejects writes to expired sessions."""
    chat_session = await _get_session_or_404(payload.session_id, db)
    if _is_expired(chat_session):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Session has expired",
        )

    message = Message(
        session_id=payload.session_id,
        role=payload.role,
        content=payload.content,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return MessageRead.model_validate(message)


@router.get("", response_model=list[MessageRead])
async def list_messages(
    session_id: str = Query(..., description="Conversation id to load history for"),
    db: AsyncSession = Depends(get_session),
) -> list[MessageRead]:
    """Return all messages for a session, oldest first."""
    await _get_session_or_404(session_id, db)

    result = await db.exec(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.all()
    return [MessageRead.model_validate(message) for message in messages]
