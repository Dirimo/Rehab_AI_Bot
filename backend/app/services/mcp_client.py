# Client de connexion au serveur MCP (FastMCP)


import json
import logging
import time
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Configuration des outils au format attendu par Ollama
OLLAMA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_exercises",
            "description": "Recherche d'exercices de rééducation (Physiopedia EN→FR, Axomove FR, exercices locaux).",
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
            "description": "Sources fiables: HAS (recommandations FR), VIDAL (fiches pathologie FR), PMC (articles scientifiques EN→FR).",
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
            "description": "Conseils de rééducation par zone anatomique (Ameli.fr parcours patient, HAS/VIDAL recommandations).",
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
    """Exception levée en cas d'échec d'un appel d'outil MCP."""


class MCPClient:
    def __init__(self, base_url=None, timeout_seconds=30.0):
        self.base_url = (base_url or settings.MCP_BASE_URL).rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def is_available(self):
        """Vérifie si le serveur MCP répond."""
        try:
            from fastmcp import Client

            async with Client(f"{self.base_url}/mcp") as client:
                await client.list_tools()
            return True
        except Exception as exc:
            logger.warning("MCP server unreachable: %s", exc)
            return False

    async def call_tool(self, name, arguments):
        """Appelle un outil MCP via le client FastMCP."""
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
            logger.warning("MCP tool %s failed after %dms: %s", name, duration_ms, exc)
            return {
                "tool": name,
                "arguments": arguments,
                "result": {"error": str(exc)},
                "status": "error",
                "duration_ms": duration_ms,
            }

    @staticmethod
    def tool_result_content(payload):
        """Formate le résultat pour le renvoyer à Ollama."""
        return json.dumps(payload.get("result", payload), ensure_ascii=False)
