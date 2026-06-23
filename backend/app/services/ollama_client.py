"""HTTP client for the local Ollama API (Member 2 → Member 4).

Ollama exposes a REST API (default http://localhost:11434). We call:
  POST /api/chat   — send messages, get assistant reply (optionally with tool_calls)
  GET  /api/tags   — list installed models (used for health checks)

Docs (Context7 / ollama.com): stream defaults to true, so we always pass stream=false
for the non-streaming path used by the agent loop's first iteration.
"""

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Raised when Ollama is unreachable or returns an error response."""


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout_seconds = timeout_seconds or settings.OLLAMA_TIMEOUT_SECONDS
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Return a shared httpx client, creating it lazily."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout_seconds,
            )
        return self._client

    async def close(self) -> None:
        """Close the shared httpx client (call on shutdown)."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def is_available(self) -> bool:
        """True if Ollama responds on /api/tags (model may still need to be pulled)."""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        """One chat completion. Returns the full Ollama JSON response."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "think": settings.OLLAMA_THINK,
            "options": {
                "num_predict": settings.OLLAMA_NUM_PREDICT,
            },
        }
        if tools:
            payload["tools"] = tools

        try:
            client = await self._get_client()
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise OllamaError(f"Ollama chat request failed: {exc}") from exc

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream chat chunks from Ollama (one JSON object per line)."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "think": settings.OLLAMA_THINK,
            "options": {
                "num_predict": settings.OLLAMA_NUM_PREDICT,
            },
        }
        if tools:
            payload["tools"] = tools

        try:
            client = await self._get_client()
            async with client.stream(
                "POST",
                "/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    yield json.loads(line)
        except httpx.HTTPError as exc:
            raise OllamaError(f"Ollama stream request failed: {exc}") from exc
