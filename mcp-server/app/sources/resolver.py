"""Resolve catalog entries to structured article payloads."""

from __future__ import annotations

from urllib.parse import urlparse

from app.scraping.fetcher import fetch_bytes, fetch_html
from app.scraping.parser import extract_article
from app.scraping.pdf_text import extract_pdf_text
from app.sources.registry import SourceEntry


async def fetch_source_entry(entry: SourceEntry) -> dict:
    """Fetch one catalog entry (HTML or PDF) into the standard article shape."""
    if entry.kind == "pdf":
        data = await fetch_bytes(entry.url)
        content = extract_pdf_text(data)
        title = entry.key.replace("_", " ").title()
        return {
            "title": title,
            "source": urlparse(entry.url).netloc,
            "url": entry.url,
            "content": content,
            "provider": entry.provider,
            "from_cache_hint": False,
        }

    html = await fetch_html(entry.url, allow_stale=True)
    article = extract_article(html, entry.url)
    article["provider"] = entry.provider
    return article
