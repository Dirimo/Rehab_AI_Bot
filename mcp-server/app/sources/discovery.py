"""Dynamic web discovery via Firecrawl, restricted to curated medical domains."""

from __future__ import annotations

import json
import logging
from urllib.parse import urlparse

from app.config import settings
from app.scraping.cache import get_cached, set_cached
from app.scraping.firecrawl_client import search_web

logger = logging.getLogger(__name__)

_CACHE_TTL = 7 * 24 * 3600

_GUIDELINE_DOMAINS = ("has-sante.fr", "vidal.fr", "ameli.fr")
_EXERCISE_DOMAINS = ("physio-pedia.com", "axomove.com")

_REHAB_HINTS = (
    "rééducation",
    "reeducation",
    "kinésithérapie",
    "kinesitherapie",
    "physiotherapy",
    "rehabilitation",
    "exercice",
)


def _root_domains(domains: tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    roots: list[str] = []
    for domain in domains:
        root = domain.removeprefix("www.")
        if root not in seen:
            seen.add(root)
            roots.append(root)
    return roots


def _domain_allowed(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in settings.ALLOWED_DOMAINS)


def _provider_for_url(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "has-sante" in host:
        return "HAS"
    if "vidal" in host:
        return "VIDAL"
    if "ameli" in host:
        return "Ameli.fr"
    if "physio-pedia" in host or "physiopedia" in host:
        return "Physiopedia"
    if "axomove" in host:
        return "Axomove"
    return "Web"


def _rehab_query(query: str) -> str:
    q = query.strip()
    if not q:
        return "rééducation kinésithérapie"
    low = q.lower()
    if any(hint in low for hint in _REHAB_HINTS):
        return q
    return f"{q} rééducation kinésithérapie"


def dynamic_search_available() -> bool:
    return bool(
        settings.DYNAMIC_SEARCH_ENABLED
        and settings.FIRECRAWL_ENABLED
        and settings.FIRECRAWL_API_KEY
    )


async def _cached_search(cache_key: str, query: str, *, limit: int, domains: list[str]) -> list[dict]:
    cached = get_cached(cache_key, _CACHE_TTL)
    if isinstance(cached, str):
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            pass

    hits = await search_web(query, limit=limit, include_domains=domains, country="FR")
    filtered: list[dict] = []
    for hit in hits:
        url = hit.get("url", "")
        if not url or not _domain_allowed(url):
            continue
        filtered.append(
            {
                "title": hit.get("title") or url,
                "url": url,
                "snippet": (hit.get("description") or "")[:500],
                "provider": _provider_for_url(url),
                "discovery": True,
            }
        )

    if filtered:
        set_cached(cache_key, json.dumps(filtered, ensure_ascii=False))
    return filtered


async def discover_guideline_sources(query: str, *, limit: int = 3) -> list[dict]:
    """Find HAS / VIDAL / Ameli pages not already in the static catalog."""
    if not dynamic_search_available():
        return []

    domains = _root_domains(_GUIDELINE_DOMAINS)
    rehab_q = _rehab_query(query)
    cache_key = f"discovery:v2:guidelines:{rehab_q}:{limit}"
    return await _cached_search(cache_key, rehab_q, limit=limit, domains=domains)


async def discover_exercise_sources(query: str, *, limit: int = 2) -> list[dict]:
    """Find Physiopedia / Axomove exercise pages via web search."""
    if not dynamic_search_available():
        return []

    domains = _root_domains(_EXERCISE_DOMAINS)
    rehab_q = _rehab_query(f"{query} exercices")
    cache_key = f"discovery:v2:exercises:{rehab_q}:{limit}"
    return await _cached_search(cache_key, rehab_q, limit=limit, domains=domains)
