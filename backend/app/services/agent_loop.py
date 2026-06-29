# Boucle principale de l'agent IA (RehabBot)
# Gère l'historique en base de données, l'envoi à Ollama et l'appel des outils MCP.


import json
import logging
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
    Session as ChatSession,
)
from app.prompts.system import SYSTEM_PROMPT
from app.services.mcp_client import MCPClient, OLLAMA_TOOLS
from app.services.ollama_client import OllamaClient, OllamaError

logger = logging.getLogger(__name__)

# États de statut pour le frontend
STATUS_THINKING = "thinking"
STATUS_SEARCHING = "searching"
STATUS_ANSWER = "answer"


class AgentLoopError(Exception):
    """Exception levée en cas d'erreur de la boucle d'agent."""


class AgentLoop:
    def __init__(self, db, ollama=None, mcp=None):
        self.db = db
        self.ollama = ollama or OllamaClient()
        self.mcp = mcp or MCPClient()

    async def run(self, session_id, user_content, on_status=None):
        """Lance la boucle d'agent pour traiter le message de l'utilisateur."""
        logger.info("Agent loop started for session %s", session_id)
        await self._emit(STATUS_THINKING, on_status)

        if not await self.ollama.is_available():
            raise AgentLoopError(
                "Ollama n'est pas disponible. Installez Ollama et lancez "
                f"`ollama pull {settings.OLLAMA_MODEL}`."
            )

        # Sauvegarde du message utilisateur (commit reporté à la fin)
        user_message = Message(
            session_id=session_id,
            role=ROLE_USER,
            content=user_content,
        )
        self.db.add(user_message)

        # Set session title based on first user message if not already set
        chat_session = await self.db.get(ChatSession, session_id)
        if chat_session and not chat_session.title:
            chat_session.title = user_content[:45] + ("..." if len(user_content) > 45 else "")
            self.db.add(chat_session)

        # Construction du contexte pour Ollama
        history = await self._load_history(session_id)
        ollama_messages = self._build_context(history)
        # Ajouter le nouveau message utilisateur au contexte Ollama
        ollama_messages.append({"role": ROLE_USER, "content": user_content})

        final_content = ""
        tool_rounds = 0

        while tool_rounds <= settings.AGENT_MAX_TOOL_ROUNDS:
            use_tools = tool_rounds < settings.AGENT_MAX_TOOL_ROUNDS
            try:
                response = await self.ollama.chat(
                    ollama_messages,
                    tools=OLLAMA_TOOLS if use_tools else None,
                    stream=False,
                )
            except OllamaError as exc:
                logger.error("Ollama chat failed for session %s: %s", session_id, exc)
                raise AgentLoopError(str(exc)) from exc

            assistant_message = response.get("message", {})
            tool_calls = assistant_message.get("tool_calls") or []
            final_content = self._extract_content(assistant_message)

            if not tool_calls:
                break

            # Si le modèle veut appeler un outil MCP
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

                logger.info("Calling MCP tool %s(%s)", tool_name, arguments)
                payload = await self.mcp.call_tool(tool_name, arguments)
                logger.info(
                    "Tool %s → %s in %dms",
                    tool_name,
                    payload.get("status", "unknown"),
                    payload.get("duration_ms", 0),
                )
                # Log tool call (commit reporté à la fin)
                self._add_tool_log(session_id, payload)

                # Format attendu par Ollama : on intègre le nom de l'outil dans le contenu
                result_content = self.mcp.tool_result_content(payload)
                ollama_messages.append(
                    {
                        "role": ROLE_TOOL,
                        "content": f"[Tool: {tool_name}]\n{result_content}",
                    }
                )

            await self._emit(STATUS_THINKING, on_status)

        # Si on dépasse le nombre de rounds d'outils max sans réponse
        if not final_content:
            await self._emit(STATUS_THINKING, on_status)
            try:
                response = await self.ollama.chat(
                    ollama_messages,
                    tools=None,
                    stream=False,
                )
                final_content = self._extract_content(response.get("message", {}))
            except OllamaError as exc:
                logger.error("Ollama final chat failed for session %s: %s", session_id, exc)
                raise AgentLoopError(str(exc)) from exc

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

        # Un seul commit pour tout : message user + tool logs + réponse assistant
        await self.db.commit()
        logger.info(
            "Agent loop completed for session %s, reply length=%d",
            session_id,
            len(final_content),
        )

        return final_content

    async def _load_history(self, session_id):
        result = await self.db.exec(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
        )
        rows = result.all()
        
        max_messages = settings.AGENT_MAX_HISTORY_MESSAGES
        max_chars = 12000  # Approx ~3000 tokens
        
        kept_rows = []
        current_chars = 0
        
        for row in rows:
            if len(kept_rows) >= max_messages:
                break
            
            # If adding this message exceeds the limit, stop
            if current_chars + len(row.content) > max_chars and kept_rows:
                break
                
            kept_rows.append(row)
            current_chars += len(row.content)
            
        # Reverse back to chronological order (oldest first)
        return kept_rows[::-1]

    def _build_context(self, history):
        messages = [
            {"role": ROLE_SYSTEM, "content": SYSTEM_PROMPT},
        ]
        for row in history:
            if row.role == ROLE_SYSTEM:
                continue
            messages.append({"role": row.role, "content": row.content})
        return messages

    def _add_tool_log(self, session_id, payload):
        """Add a tool log record (not committed yet — batched with final commit)."""
        log = ToolLog(
            session_id=session_id,
            tool_name=payload.get("tool", "unknown"),
            arguments=payload.get("arguments", {}),
            result=payload.get("result", {}),
            status=payload.get("status", "success"),
            duration_ms=payload.get("duration_ms"),
        )
        self.db.add(log)

    @staticmethod
    def _extract_content(message):
        content = (message.get("content") or "").strip()
        if content:
            return content
        return ""

    @staticmethod
    def _parse_tool_arguments(raw_args):
        if isinstance(raw_args, dict):
            return raw_args
        if isinstance(raw_args, str) and raw_args.strip():
            try:
                return json.loads(raw_args)
            except json.JSONDecodeError:
                logger.warning("Malformed tool arguments from LLM: %s", raw_args[:200])
                return {"raw": raw_args}
        return {}

    @staticmethod
    async def _emit(status, callback):
        if callback is not None:
            await callback(status)
