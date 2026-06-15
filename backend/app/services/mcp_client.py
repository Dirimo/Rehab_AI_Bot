"""MCP tool client (Member 2 → Member 3).

Member 3 will run a FastMCP server (port 8001) exposing scraping tools.
For now this client:
  - defines the tool schemas we send to Ollama
  - returns a clear stub response when the MCP server is not reachable

When Member 3's server exists, we will call:
  fastmcp.Client(f"{MCP_BASE_URL}/mcp").call_tool(name, arguments)
"""

import json
import time
from typing import Any

import httpx

from app.config import settings

# Tool schemas in Ollama's "tools" format (JSON Schema parameters).
OLLAMA_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_exercises",
            "description": "Recherche d'exercices de rééducation par pathologie ou zone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Pathologie ou zone (ex: lombalgie, épaule)",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_sources",
            "description": "Recherche de sources médicales fiables (HAS, Ameli, Vidal).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Sujet à rechercher",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rehab_advice",
            "description": "Conseils généraux de rééducation par zone anatomique.",
            "parameters": {
                "type": "object",
                "properties": {
                    "body_zone": {
                        "type": "string",
                        "description": "Zone du corps (ex: dos, genou, épaule)",
                    }
                },
                "required": ["body_zone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_article",
            "description": "Extrait le contenu d'un article depuis une URL publique.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL de l'article à extraire",
                    }
                },
                "required": ["url"],
            },
        },
    },
]


class MCPError(Exception):
    """Raised when an MCP tool call fails."""


class MCPClient:
    def __init__(self, base_url: str | None = None, timeout_seconds: float = 30.0) -> None:
        self.base_url = (base_url or settings.MCP_BASE_URL).rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def is_available(self) -> bool:
        """Best-effort check — real MCP server will expose /mcp (Member 3)."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call one MCP tool. Falls back to a stub if the server is not up yet."""
        started = time.perf_counter()

        # TODO (Member 3): replace with fastmcp.Client(f"{self.base_url}/mcp")
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/tools/{name}",
                    json=arguments,
                )
                response.raise_for_status()
                payload = response.json()
                duration_ms = int((time.perf_counter() - started) * 1000)
                return {
                    "tool": name,
                    "arguments": arguments,
                    "result": payload,
                    "status": "success",
                    "duration_ms": duration_ms,
                }
        except httpx.HTTPError as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            return {
                "tool": name,
                "arguments": arguments,
                "result": {
                    "stub": True,
                    "message": (
                        "Serveur MCP non disponible pour l'instant. "
                        "Member 3 doit démarrer le serveur FastMCP."
                    ),
                    "error": str(exc),
                },
                "status": "error",
                "duration_ms": duration_ms,
            }

    @staticmethod
    def tool_result_content(payload: dict[str, Any]) -> str:
        """Serialize tool output for the 'tool' role message sent back to Ollama."""
        return json.dumps(payload.get("result", payload), ensure_ascii=False)
