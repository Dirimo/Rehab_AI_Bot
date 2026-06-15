"""HTTP client for the local Ollama API (Member 2 → Member 4).

Ollama exposes a REST API (default http://localhost:11434). We call:
  POST /api/chat   — send messages, get assistant reply (optionally with tool_calls)
  GET  /api/tags   — list installed models (used for health checks)

Docs (Context7 / ollama.com): stream defaults to true, so we always pass stream=false
for the non-streaming path used by the agent loop's first iteration.
"""

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.config import settings


class OllamaError(Exception):
    """Raised when Ollama is unreachable or returns an error response."""


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout_seconds = timeout_seconds

    async def is_available(self) -> bool:
        """True if Ollama responds on /api/tags (model may still need to be pulled)."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
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
        }
        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
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
        }
        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        yield json.loads(line)
        except httpx.HTTPError as exc:
            raise OllamaError(f"Ollama stream request failed: {exc}") from exc
