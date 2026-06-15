"""WebSocket chat route (Member 2 → Member 1 real-time streaming).

The frontend connects to:  ws://localhost:8000/ws/chat

Protocol
--------
Client sends (JSON):
  {"session_id": "abc123", "content": "J'ai mal au dos"}

Server sends (JSON events):
  {"type": "status", "status": "thinking"}    → agent is processing
  {"type": "status", "status": "searching"}   → MCP tool is running
  {"type": "status", "status": "answer"}        → reply is ready
  {"type": "message", "reply": "...", "status": "completed"}
  {"type": "error", "detail": "..."}
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import async_session_maker
from app.models import Session as ChatSession
from app.routers.messages import _is_expired
from app.services.agent_loop import AgentLoop, AgentLoopError

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket) -> None:
    """Persistent connection: one user message in, status events + reply out."""
    await websocket.accept()

    try:
        while True:
            payload = await websocket.receive_json()
            session_id = payload.get("session_id", "").strip()
            content = payload.get("content", "").strip()

            if not session_id or not content:
                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": "session_id and content are required",
                    }
                )
                continue

            async with async_session_maker() as db:
                if not await _handle_message(websocket, db, session_id, content):
                    continue
    except WebSocketDisconnect:
        return


async def _handle_message(
    websocket: WebSocket,
    db: AsyncSession,
    session_id: str,
    content: str,
) -> bool:
    """Run one chat turn. Returns False if the client should retry on same socket."""
    chat_session = await db.get(ChatSession, session_id)
    if chat_session is None:
        await websocket.send_json({"type": "error", "detail": "Session not found"})
        return False

    if _is_expired(chat_session):
        await websocket.send_json({"type": "error", "detail": "Session has expired"})
        return False

    async def on_status(status: str) -> None:
        await websocket.send_json({"type": "status", "status": status})

    agent = AgentLoop(db)
    try:
        reply = await agent.run(session_id, content, on_status=on_status)
    except AgentLoopError as exc:
        await websocket.send_json({"type": "error", "detail": str(exc)})
        return False

    await websocket.send_json(
        {
            "type": "message",
            "reply": reply,
            "status": "completed",
        }
    )
    return True
