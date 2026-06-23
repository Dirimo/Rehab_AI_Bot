# Serveur MCP pour RehabBot - Projet d'étudiant EPITECH


from fastmcp import FastMCP

from app.config import settings
from app.scraping.fetcher import fetch_html
from app.scraping.parser import extract_article
from app.sources.ameli import get_ameli_advice
from app.sources.axomove import search_axomove_exercises
from app.sources.discovery import discover_exercise_sources, discover_guideline_sources, dynamic_search_available
from app.sources.local_exercises import search_exercises as search_local_exercises
from app.sources.physiopedia import search_physiopedia_exercises
from app.sources.pmc import search_pmc_articles
from app.sources.registry import SOURCE_CATALOG, get_by_key, match_sources
from app.sources.resolver import fetch_source_entry

mcp = FastMCP("RehabBot MCP")


def _error_payload(tool, detail):
    return {"error": True, "tool": tool, "detail": detail}


def _format_exercise_item(ex):
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
    """Recherche des exercices de rééducation par zone ou pathologie."""
    try:
        items = []

        # 1) Recherche dans les exercices locaux
        for ex in search_local_exercises(query, limit=3):
            items.append(_format_exercise_item(ex))

        # 2) Recherche sur Physiopedia (EN, à traduire)
        try:
            for article in await search_physiopedia_exercises(query, limit=2, translate=True):
                items.append(
                    {
                        "title": article["title"],
                        "content": article["content"][:2500],
                        "url": article["url"],
                        "provider": article.get("provider", "Physiopedia"),
                    }
                )
        except Exception:
            pass

        # 3) Recherche sur Axomove
        try:
            for article in await search_axomove_exercises(query, limit=2):
                items.append(
                    {
                        "title": article["title"],
                        "content": article["content"][:2500],
                        "url": article["url"],
                        "provider": article.get("provider", "Axomove"),
                    }
                )
        except Exception:
            pass

        # 4) Découverte web dynamique si pas assez de résultats locaux
        web_items = [it for it in items if it.get("provider") in ("Physiopedia", "Axomove")]
        if dynamic_search_available() and len(web_items) < settings.DYNAMIC_SEARCH_MIN_CATALOG_HITS:
            try:
                seen_urls = {it.get("url") for it in items if it.get("url")}
                for hit in await discover_exercise_sources(query, limit=2):
                    url = hit.get("url", "")
                    if not url or url in seen_urls:
                        continue
                    article = extract_article(await fetch_html(url), url)
                    content = article.get("content", "")
                    if len(content) < 200:
                        continue
                    provider = hit.get("provider", "Web")
                    if provider == "Physiopedia":
                        from app.scraping.translator import translate_en_to_fr

                        content = await translate_en_to_fr(content[:2500])
                    items.append(
                        {
                            "title": article.get("title") or hit.get("title"),
                            "content": content[:2500],
                            "url": url,
                            "provider": provider,
                        }
                    )
                    seen_urls.add(url)
            except Exception:
                pass

        if items:
            providers = sorted({it.get("provider", "?") for it in items})
            note = "Sources: Physiopedia (traduit EN→FR), Axomove, exercices locaux."
            if dynamic_search_available():
                note += " Découverte web (domaines autorisés) activée."
            return {
                "query": query,
                "items": items,
                "sources_used": providers,
                "note": note,
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
    """Recherche des sources médicales fiables (HAS, VIDAL, PMC)."""
    try:
        sources = []

        # HAS + VIDAL depuis le catalogue statique
        for entry in match_sources(query, limit=4):
            sources.append(
                {
                    "title": entry.key.replace("_", " ").title(),
                    "url": entry.url,
                    "provider": entry.provider,
                    "zone": entry.zone,
                }
            )

        # Articles scientifiques PMC (traduits EN -> FR)
        try:
            for article in await search_pmc_articles(query, limit=3, translate=True):
                sources.append(
                    {
                        "title": article.get("title", "Article PMC"),
                        "url": article.get("url", ""),
                        "snippet": article.get("abstract", "")[:500],
                        "provider": article.get("provider", "PMC (PubMed Central)"),
                        "authors": article.get("authors", ""),
                    }
                )
        except Exception:
            pass

        catalog_hits = [s for s in sources if s.get("provider") in ("HAS", "VIDAL", "Ameli.fr")]
        if dynamic_search_available() and len(catalog_hits) < settings.DYNAMIC_SEARCH_MIN_CATALOG_HITS:
            try:
                seen_urls = {s.get("url") for s in sources if s.get("url")}
                for hit in await discover_guideline_sources(query, limit=3):
                    url = hit.get("url", "")
                    if url and url not in seen_urls:
                        sources.append(hit)
                        seen_urls.add(url)
            except Exception:
                pass

        if not sources and dynamic_search_available():
            try:
                sources = await discover_guideline_sources(query, limit=4)
            except Exception:
                pass

        if not sources:
            return {
                "query": query,
                "sources": [],
                "catalog_topics": [e.key for e in SOURCE_CATALOG],
                "note": "Essayez: dos, genou, épaule, arthrose, parkinson, hanche.",
            }

        # Déduplication par URL
        seen = set()
        unique = []
        for src in sources:
            url = src.get("url", "")
            if url and url not in seen:
                seen.add(url)
                unique.append(src)

        return {"query": query, "sources": unique, "dynamic_search": dynamic_search_available()}
    except Exception as exc:
        return _error_payload("search_sources", str(exc))


@mcp.tool
async def get_rehab_advice(body_zone: str) -> dict:
    """Conseils généraux et parcours de soins par zone du corps."""
    try:
        key = body_zone.strip().lower()

        # 1) Conseils Ameli.fr
        ameli_result = None
        try:
            ameli_result = await get_ameli_advice(key)
        except Exception:
            pass

        # 2) Recherche dans le catalogue HAS / VIDAL
        entry = get_by_key(key) or next(iter(match_sources(key, limit=1)), None)
        catalog_article = None
        if entry is not None:
            try:
                catalog_article = await fetch_source_entry(entry)
            except Exception:
                pass

        # 3) Recherche dynamique en cas d'échec
        discovered = None
        if not ameli_result and not catalog_article and dynamic_search_available():
            try:
                for hit in await discover_guideline_sources(key, limit=2):
                    url = hit.get("url", "")
                    if not url:
                        continue
                    article = extract_article(await fetch_html(url), url)
                    if len(article.get("content", "")) < 200:
                        continue
                    discovered = {
                        "title": article.get("title") or hit.get("title", ""),
                        "content": article.get("content", "")[:3000],
                        "url": url,
                        "provider": hit.get("provider", "Web"),
                    }
                    break
            except Exception:
                pass

        # 4) Exercices associés à la zone
        local = search_local_exercises(key, limit=3)
        exercise_hints = [_format_exercise_item(ex) for ex in local]

        if not ameli_result and not catalog_article and not discovered:
            return _error_payload(
                "get_rehab_advice",
                f"Zone inconnue: {body_zone}. Essayez: dos, genou, epaule, cheville, hanche, cou.",
            )

        result = {"body_zone": body_zone, "suggested_exercises": exercise_hints}

        if ameli_result:
            result["ameli"] = {
                "title": ameli_result.get("title", ""),
                "content": ameli_result.get("content", "")[:3000],
                "url": ameli_result.get("url", ""),
                "provider": "Ameli.fr",
            }

        if catalog_article:
            result["guideline"] = {
                "title": catalog_article.get("title", ""),
                "content": catalog_article.get("content", "")[:3000],
                "url": catalog_article.get("url", ""),
                "provider": entry.provider if entry else "HAS/VIDAL",
            }
        elif discovered:
            result["guideline"] = discovered

        return result
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
