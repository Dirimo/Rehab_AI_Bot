"""MCP tool client (Member 2 → Member 3).

Calls the FastMCP HTTP server started by Member 3:
  fastmcp.Client("http://localhost:8001/mcp").call_tool(name, arguments)
"""

import json
import time
from typing import Any

from app.config import settings

# Tool schemas in Ollama's "tools" format (JSON Schema parameters).
OLLAMA_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_exercises",
            "description": "Recherche d'exercices (bundle local NHS/MedlinePlus + HAS, NHS, MedlinePlus en cache).",
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
            "description": "Sources fiables: HAS, Santé publique France, NHS, MedlinePlus (API), CSP, VIDAL.",
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
        """Check that the MCP HTTP endpoint responds and exposes tools."""
        try:
            from fastmcp import Client

            async with Client(f"{self.base_url}/mcp") as client:
                await client.list_tools()
            return True
        except Exception:
            return False

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call one MCP tool via the FastMCP HTTP client."""
        started = time.perf_counter()
        try:
            from fastmcp import Client

            async with Client(f"{self.base_url}/mcp") as client:
                result = await client.call_tool(name, arguments)

            if result.is_error:
                raise MCPError(f"MCP tool {name} failed")

            payload = result.structured_content or {}
            if not payload and result.content:
                texts = [
                    getattr(block, "text", str(block))
                    for block in result.content
                ]
                payload = {"text": "\n".join(texts)}

            duration_ms = int((time.perf_counter() - started) * 1000)
            return {
                "tool": name,
                "arguments": arguments,
                "result": payload,
                "status": "success",
                "duration_ms": duration_ms,
            }
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            return {
                "tool": name,
                "arguments": arguments,
                "result": {"error": str(exc)},
                "status": "error",
                "duration_ms": duration_ms,
            }

    @staticmethod
    def tool_result_content(payload: dict[str, Any]) -> str:
        """Serialize tool output for the 'tool' role message sent back to Ollama."""
        return json.dumps(payload.get("result", payload), ensure_ascii=False)
