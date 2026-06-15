"""RehabBot MCP server — exposes scraping tools to the backend (Member 3).

Start with:
    python run.py

The backend (Member 2) connects via:
    fastmcp.Client("http://localhost:8001/mcp")
"""

from __future__ import annotations

from fastmcp import FastMCP

from app.config import settings
from app.scraping.fetcher import fetch_html
from app.scraping.parser import extract_article
from app.sources.local_exercises import search_exercises as search_local_exercises
from app.sources.medlineplus import search_health_topics
from app.sources.registry import SOURCE_CATALOG, get_by_key, match_sources
from app.sources.resolver import fetch_source_entry

mcp = FastMCP("RehabBot MCP")


def _error_payload(tool: str, detail: str) -> dict:
    return {"error": True, "tool": tool, "detail": detail}


def _format_exercise_item(ex: dict) -> dict:
    instructions = ex.get("instructions", [])
    return {
        "title": ex.get("name", "Exercice"),
        "content": "\n".join(f"- {step}" for step in instructions),
        "sets": ex.get("sets", ""),
        "zone": ex.get("zone", ""),
        "url": ex.get("source_url", ""),
        "provider": ex.get("provider", "bundled"),
    }


@mcp.tool
async def search_exercises(query: str) -> dict:
    """Recherche d'exercices de rééducation par pathologie ou zone anatomique."""
    try:
        items: list[dict] = []

        # 1) Offline bundle — never blocked, instant.
        for ex in search_local_exercises(query, limit=4):
            items.append(_format_exercise_item(ex))

        # 2) Curated remote pages (HAS, NHS, MedlinePlus…) via cache.
        for entry in match_sources(query, limit=2):
            if entry.kind == "pdf":
                continue
            try:
                article = await fetch_source_entry(entry)
                items.append(
                    {
                        "title": article["title"],
                        "content": article["content"][:2500],
                        "url": article["url"],
                        "provider": article.get("provider", entry.provider),
                    }
                )
            except Exception:
                continue

        if items:
            providers = sorted({it.get("provider", "?") for it in items})
            return {
                "query": query,
                "items": items,
                "sources_used": providers,
                "note": "Mélange données locales (NHS/MedlinePlus résumés) + pages publiques en cache.",
            }

        return {
            "query": query,
            "items": [],
            "note": (
                "Aucun exercice trouvé. Essayez: dos, lombalgie, genou, épaule, "
                "cheville, hanche, coiffe."
            ),
        }
    except Exception as exc:
        return _error_payload("search_exercises", str(exc))


@mcp.tool
async def search_sources(query: str) -> dict:
    """Recherche de sources fiables (HAS, NHS, MedlinePlus, Santé publique France…)."""
    try:
        sources: list[dict] = []

        # Curated catalog (French + international).
        for entry in match_sources(query, limit=4):
            sources.append(
                {
                    "title": entry.key.replace("_", " ").title(),
                    "url": entry.url,
                    "provider": entry.provider,
                    "zone": entry.zone,
                }
            )

        # MedlinePlus API — official, no scraping.
        try:
            for hit in await search_health_topics(query, limit=3):
                sources.append(hit)
        except Exception:
            pass

        if not sources:
            return {
                "query": query,
                "sources": [],
                "catalog_topics": [e.key for e in SOURCE_CATALOG],
                "note": "Essayez: dos, genou, épaule, tms, parkinson, hanche.",
            }

        # Deduplicate by URL.
        seen: set[str] = set()
        unique: list[dict] = []
        for src in sources:
            url = src.get("url", "")
            if url and url not in seen:
                seen.add(url)
                unique.append(src)

        return {"query": query, "sources": unique}
    except Exception as exc:
        return _error_payload("search_sources", str(exc))


@mcp.tool
async def get_rehab_advice(body_zone: str) -> dict:
    """Conseils généraux de rééducation pour une zone anatomique."""
    try:
        key = body_zone.strip().lower()
        entry = get_by_key(key) or next(iter(match_sources(key, limit=1)), None)
        if entry is None:
            return _error_payload(
                "get_rehab_advice",
                f"Zone inconnue: {body_zone}. Essayez: dos, genou, epaule, cheville, hanche, cou.",
            )

        article = await fetch_source_entry(entry)
        local = search_local_exercises(key, limit=3)
        exercise_hints = [_format_exercise_item(ex) for ex in local]

        return {
            "body_zone": body_zone,
            "provider": entry.provider,
            **article,
            "suggested_exercises": exercise_hints,
        }
    except Exception as exc:
        return _error_payload("get_rehab_advice", str(exc))


@mcp.tool
async def scrape_article(url: str) -> dict:
    """Extrait le contenu d'un article public depuis une URL autorisée (cache 7 jours)."""
    try:
        if url.lower().endswith(".pdf"):
            from app.scraping.fetcher import fetch_bytes
            from app.scraping.pdf_text import extract_pdf_text

            content = extract_pdf_text(await fetch_bytes(url))
            return {
                "title": "Document PDF",
                "source": url.split("/")[2],
                "url": url,
                "content": content,
            }
        article = extract_article(await fetch_html(url), url)
        return article
    except Exception as exc:
        return _error_payload("scrape_article", str(exc))


if __name__ == "__main__":
    mcp.run(transport="http", host=settings.MCP_HOST, port=settings.MCP_PORT)
