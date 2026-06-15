"""Chat route — triggers the agent loop (Member 2 orchestration).

This is the main "ask RehabBot a question" endpoint.
WebSocket streaming will be added next; for now this returns the full reply.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.routers.messages import _get_session_or_404, _is_expired
from app.schemas import ChatRequest, ChatResponse
from app.services.agent_loop import AgentLoop, AgentLoopError

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_session),
) -> ChatResponse:
    """Send a user message and run the agent loop to get RehabBot's reply."""
    chat_session = await _get_session_or_404(payload.session_id, db)
    if _is_expired(chat_session):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Session has expired",
        )

    agent = AgentLoop(db)
    try:
        reply = await agent.run(payload.session_id, payload.content)
    except AgentLoopError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return ChatResponse(session_id=payload.session_id, reply=reply)
