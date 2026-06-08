"""
Client HTTP vers le serveur MCP (Membre 3) — appel des tools de scraping

► MEMBRE 3 (MCP Server / Scraping) :
    Ce fichier définit le contrat d'interface entre le backend et ton serveur MCP.
    Le backend s'attend à appeler : POST http://localhost:8001/tools/{tool_name}
    avec le body JSON correspondant aux arguments du tool.

    Exemple d'appel pour search_exercises :
        POST http://localhost:8001/tools/search_exercises
        Body : { "pathology": "tendinite rotulienne" }
        Réponse attendue (JSON) :
        {
          "exercises": [
            { "title": "...", "description": "...", "source": "...", "url": "..." }
          ]
        }

    Les 4 tools attendus et leurs arguments :
    ┌─────────────────────┬──────────────────────────────────────────┐
    │ Tool                │ Arguments requis                         │
    ├─────────────────────┼──────────────────────────────────────────┤
    │ search_exercises    │ { "pathology": string }                  │
    │ search_sources      │ { "query": string }                      │
    │ get_rehab_advice    │ { "body_zone": string }                  │
    │ scrape_article      │ { "url": string }                        │
    └─────────────────────┴──────────────────────────────────────────┘

    En cas d'erreur (page indisponible, timeout scraping, etc.), retourne :
        { "error": "description de l'erreur" }
    Le backend gère ce cas proprement sans crasher.

    Variable d'environnement : MCP_BASE_URL=http://localhost:8001 (voir .env.example)

► MEMBRE 4 (LLM / Prompts) :
    La liste AVAILABLE_TOOLS ci-dessous est transmise à Ollama dans chaque requête.
    C'est ce qui permet au modèle de savoir quels tools appeler et avec quels arguments.
    Si tu modifies les descriptions ou les paramètres des tools, mets à jour cette liste
    ET informe Membre 3 pour que le serveur MCP corresponde.
"""

import os
import time
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:8001")
MCP_TIMEOUT = 15.0

# Schémas des tools transmis à Ollama — format OpenAI function calling
AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_exercises",
            "description": "Recherche des exercices de rééducation selon une pathologie.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pathology": {
                        "type": "string",
                        "description": "La pathologie ou le trouble (ex: tendinite, lombalgie, entorse).",
                    }
                },
                "required": ["pathology"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_sources",
            "description": "Recherche des sources médicales fiables (HAS, Vidal, Ameli) sur un sujet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Le sujet ou la question médicale à rechercher.",
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
            "description": "Fournit des conseils généraux de rééducation pour une zone anatomique.",
            "parameters": {
                "type": "object",
                "properties": {
                    "body_zone": {
                        "type": "string",
                        "description": "La zone anatomique concernée (ex: épaule, genou, dos).",
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
            "description": "Extrait le contenu d'un article médical depuis une URL publique.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "L'URL publique de l'article à extraire.",
                    }
                },
                "required": ["url"],
            },
        },
    },
]


async def call_tool(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """
    Appelle un tool sur le serveur MCP.
    Retourne { "result": {...}, "duration_ms": int, "input": {...} }
    En cas d'erreur, result contiendra { "error": "..." } sans lever d'exception.
    """
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=MCP_TIMEOUT) as client:
            response = await client.post(
                f"{MCP_BASE_URL}/tools/{tool_name}",
                json=tool_input,
            )
            response.raise_for_status()
            result = response.json()
    except httpx.TimeoutException:
        result = {"error": f"Le tool '{tool_name}' n'a pas répondu dans les {MCP_TIMEOUT}s"}
    except httpx.HTTPStatusError as e:
        result = {"error": f"Le tool '{tool_name}' a retourné HTTP {e.response.status_code}"}
    except Exception as e:
        result = {"error": f"Erreur inattendue sur le tool '{tool_name}' : {str(e)}"}

    duration_ms = int((time.monotonic() - start) * 1000)
    return {"result": result, "duration_ms": duration_ms, "input": tool_input}
