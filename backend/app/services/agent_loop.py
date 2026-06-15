"""Agent loop — the orchestration brain of RehabBot (Member 2).

This is the core flow from the PDF spec:

  1. Load conversation history from PostgreSQL
  2. Build context: system prompt + history + new user message
  3. Send context to Ollama (Member 4)
  4. If the model emits tool_calls → call MCP server (Member 3)
  5. Re-inject tool results into context and ask Ollama again
  6. Save the final assistant reply to the database

Status events ("thinking", "searching", "answer") are emitted via an optional
callback so the WebSocket route (next step) can stream them to the frontend.
"""

import json
from collections.abc import Awaitable, Callable
from typing import Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.models import (
    ROLE_ASSISTANT,
    ROLE_SYSTEM,
    ROLE_TOOL,
    ROLE_USER,
    Message,
    ToolLog,
)
from app.prompts.system import SYSTEM_PROMPT
from app.services.mcp_client import MCPClient, OLLAMA_TOOLS
from app.services.ollama_client import OllamaClient, OllamaError

# Status strings the frontend will display (Member 1).
STATUS_THINKING = "thinking"
STATUS_SEARCHING = "searching"
STATUS_ANSWER = "answer"

StatusCallback = Callable[[str], Awaitable[None]]


class AgentLoopError(Exception):
    """Raised when the agent loop cannot complete (e.g. Ollama down)."""


class AgentLoop:
    def __init__(
        self,
        db: AsyncSession,
        ollama: OllamaClient | None = None,
        mcp: MCPClient | None = None,
    ) -> None:
        self.db = db
        self.ollama = ollama or OllamaClient()
        self.mcp = mcp or MCPClient()

    async def run(
        self,
        session_id: str,
        user_content: str,
        *,
        on_status: StatusCallback | None = None,
    ) -> str:
        """Run the full agent loop and return the final assistant text."""
        await self._emit(STATUS_THINKING, on_status)

        if not await self.ollama.is_available():
            raise AgentLoopError(
                "Ollama n'est pas disponible. Installez Ollama et lancez "
                f"`ollama pull {settings.OLLAMA_MODEL}`."
            )

        # Persist the user message first (same as POST /messages).
        user_message = Message(
            session_id=session_id,
            role=ROLE_USER,
            content=user_content,
        )
        self.db.add(user_message)
        await self.db.commit()

        # Build the message list Ollama expects.
        history = await self._load_history(session_id)
        ollama_messages = self._build_context(history)

        final_content = ""
        tool_rounds = 0

        while tool_rounds <= settings.AGENT_MAX_TOOL_ROUNDS:
            try:
                response = await self.ollama.chat(
                    ollama_messages,
                    tools=OLLAMA_TOOLS,
                    stream=False,
                )
            except OllamaError as exc:
                raise AgentLoopError(str(exc)) from exc

            assistant_message = response.get("message", {})
            tool_calls = assistant_message.get("tool_calls") or []

            if not tool_calls:
                final_content = (assistant_message.get("content") or "").strip()
                break

            # Model wants to use tools — hand off to Member 3 (MCP).
            await self._emit(STATUS_SEARCHING, on_status)
            tool_rounds += 1

            ollama_messages.append(
                {
                    "role": ROLE_ASSISTANT,
                    "content": assistant_message.get("content", ""),
                    "tool_calls": tool_calls,
                }
            )

            for tool_call in tool_calls:
                function = tool_call.get("function", {})
                tool_name = function.get("name", "")
                raw_args = function.get("arguments", {})
                arguments = self._parse_tool_arguments(raw_args)

                payload = await self.mcp.call_tool(tool_name, arguments)
                await self._log_tool_call(session_id, payload)

                ollama_messages.append(
                    {
                        "role": ROLE_TOOL,
                        "content": self.mcp.tool_result_content(payload),
                    }
                )

            await self._emit(STATUS_THINKING, on_status)

        if not final_content:
            final_content = (
                "Je n'ai pas pu produire de réponse après plusieurs tentatives. "
                "Réessayez ou reformulez votre question."
            )

        await self._emit(STATUS_ANSWER, on_status)

        assistant_row = Message(
            session_id=session_id,
            role=ROLE_ASSISTANT,
            content=final_content,
        )
        self.db.add(assistant_row)
        await self.db.commit()

        return final_content

    async def _load_history(self, session_id: str) -> list[Message]:
        result = await self.db.exec(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
        )
        rows = result.all()
        max_messages = settings.AGENT_MAX_HISTORY_MESSAGES
        return rows[-max_messages:] if len(rows) > max_messages else rows

    def _build_context(self, history: list[Message]) -> list[dict[str, Any]]:
        """system prompt + recent history (roles user/assistant/tool only in DB)."""
        messages: list[dict[str, Any]] = [
            {"role": ROLE_SYSTEM, "content": SYSTEM_PROMPT},
        ]
        for row in history:
            if row.role == ROLE_SYSTEM:
                continue
            messages.append({"role": row.role, "content": row.content})
        return messages

    async def _log_tool_call(self, session_id: str, payload: dict[str, Any]) -> None:
        log = ToolLog(
            session_id=session_id,
            tool_name=payload.get("tool", "unknown"),
            arguments=payload.get("arguments", {}),
            result=payload.get("result", {}),
            status=payload.get("status", "success"),
            duration_ms=payload.get("duration_ms"),
        )
        self.db.add(log)
        await self.db.commit()

    @staticmethod
    def _parse_tool_arguments(raw_args: Any) -> dict[str, Any]:
        if isinstance(raw_args, dict):
            return raw_args
        if isinstance(raw_args, str) and raw_args.strip():
            return json.loads(raw_args)
        return {}

    @staticmethod
    async def _emit(status: str, callback: StatusCallback | None) -> None:
        if callback is not None:
            await callback(status)
