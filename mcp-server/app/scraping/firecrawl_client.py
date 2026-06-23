"""Optional Firecrawl API — scrape fallback and domain-restricted web search."""

from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_FIRECRAWL_SCRAPE_API = "https://api.firecrawl.dev/v1/scrape"
_FIRECRAWL_SEARCH_API = "https://api.firecrawl.dev/v2/search"


async def scrape_markdown(url: str) -> str | None:
    """Fetch clean markdown for *url* via Firecrawl. Returns None if disabled or on failure."""
    if not settings.FIRECRAWL_ENABLED or not settings.FIRECRAWL_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {settings.FIRECRAWL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(_FIRECRAWL_SCRAPE_API, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        if not data.get("success"):
            logger.warning("Firecrawl scrape failed for %s: %s", url, data)
            return None

        markdown = (data.get("data") or {}).get("markdown", "")
        if not isinstance(markdown, str) or len(markdown.strip()) < 100:
            return None

        metadata = (data.get("data") or {}).get("metadata") or {}
        status = metadata.get("statusCode")
        if status and int(status) >= 400:
            logger.warning("Firecrawl returned HTTP %s for %s", status, url)
            return None

        return markdown.strip()
    except Exception as exc:
        logger.warning("Firecrawl request error for %s: %s", url, exc)
        return None


async def search_web(
    query: str,
    *,
    limit: int = 5,
    include_domains: list[str] | None = None,
    country: str = "FR",
) -> list[dict]:
    """Search the web via Firecrawl, optionally restricted to *include_domains*.

    Returns dicts with: url, title, description (snippet may be absent).
  """
    if not settings.FIRECRAWL_ENABLED or not settings.FIRECRAWL_API_KEY:
        return []

    headers = {
        "Authorization": f"Bearer {settings.FIRECRAWL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "query": query,
        "limit": limit,
        "country": country,
    }
    if include_domains:
        payload["includeDomains"] = include_domains

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(_FIRECRAWL_SEARCH_API, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        if not data.get("success"):
            logger.warning("Firecrawl search failed for %r: %s", query, data)
            return []

        raw = data.get("data")
        if isinstance(raw, dict):
            web = raw.get("web") or []
        elif isinstance(raw, list):
            web = raw
        else:
            web = []
        results: list[dict] = []
        for item in web:
            if not isinstance(item, dict):
                continue
            url = item.get("url", "")
            if not url:
                continue
            results.append(
                {
                    "url": url,
                    "title": item.get("title", "") or url,
                    "description": item.get("description", "") or item.get("snippet", ""),
                }
            )
        return results
    except Exception as exc:
        logger.warning("Firecrawl search error for %r: %s", query, exc)
        return []
