"""Fetch public pages with cache, rate limits, and robots.txt awareness."""

from __future__ import annotations

import asyncio
import random
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from app.config import settings
from app.scraping.cache import get_cached, get_stale, set_cached

# Honest bot id + browser-like accept headers (many CDNs block bare httpx defaults).
USER_AGENT = (
    "Mozilla/5.0 (compatible; RehabBot-Edu/0.2; +educational-rehab-prototype; "
    "contact=local-dev) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

# Official APIs — skip robots.txt (they are meant for programmatic access).
API_HOSTS = frozenset(
    {
        "wsearch.nlm.nih.gov",
        "api.github.com",
        "raw.githubusercontent.com",
    }
)

_robots_cache: dict[str, RobotFileParser] = {}
_last_request_at: float = 0.0
_rate_lock = asyncio.Lock()
_client: httpx.AsyncClient | None = None


def _domain_allowed(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in settings.ALLOWED_DOMAINS)


def _is_api_url(url: str) -> bool:
    return urlparse(url).netloc.lower() in API_HOSTS


def _referer_for(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=30.0,
            headers=DEFAULT_HEADERS,
            follow_redirects=True,
            http2=True,
        )
    return _client


async def _respect_rate_limit() -> None:
    global _last_request_at
    async with _rate_lock:
        base = settings.SCRAPING_RATE_LIMIT_SECONDS
        jitter = random.uniform(0, settings.SCRAPING_RATE_LIMIT_JITTER_SECONDS)
        wait_for = (base + jitter) - (time.monotonic() - _last_request_at)
        if wait_for > 0:
            await asyncio.sleep(wait_for)
        _last_request_at = time.monotonic()


async def _robots_allowed(url: str) -> bool:
    if _is_api_url(url):
        return True
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if base not in _robots_cache:
        parser = RobotFileParser()
        parser.set_url(f"{base}/robots.txt")
        try:
            parser.read()
        except Exception:
            return True
        _robots_cache[base] = parser
    return _robots_cache[base].can_fetch(USER_AGENT, url)


async def _fetch_live(url: str) -> tuple[str | bytes, str]:
    """Returns (body, content_type)."""
    if not _domain_allowed(url) and not _is_api_url(url):
        raise PermissionError(f"Domain not allowed for scraping: {url}")

    if not _is_api_url(url) and not await _robots_allowed(url):
        raise PermissionError(f"robots.txt disallows fetching: {url}")

    await _respect_rate_limit()
    client = await _get_client()
    headers = {"Referer": _referer_for(url)}
    response = await client.get(url, headers=headers)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "pdf" in content_type.lower() or url.lower().endswith(".pdf"):
        return response.content, content_type
    return response.text, content_type


async def fetch_bytes(url: str, *, allow_stale: bool = True) -> bytes:
    cached = get_cached(url, settings.HTTP_CACHE_TTL_SECONDS)
    if isinstance(cached, bytes):
        return cached
    if isinstance(cached, str):
        return cached.encode("utf-8")

    try:
        body, _ = await _fetch_live(url)
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        set_cached(url, data)
        return data
    except Exception:
        if allow_stale:
            stale = get_stale(url)
            if isinstance(stale, bytes):
                return stale
            if isinstance(stale, str):
                return stale.encode("utf-8")
        raise


async def fetch_html(url: str, *, allow_stale: bool = True) -> str:
    """Fetch HTML with disk cache and stale fallback on block/errors."""
    cached = get_cached(url, settings.HTTP_CACHE_TTL_SECONDS)
    if isinstance(cached, str):
        return cached

    try:
        body, content_type = await _fetch_live(url)
        if isinstance(body, bytes):
            if "pdf" in content_type.lower() or url.lower().endswith(".pdf"):
                raise ValueError("URL is a PDF; use fetch_bytes instead")
            text = body.decode("utf-8", errors="replace")
        else:
            text = body
        set_cached(url, text)
        return text
    except Exception as exc:
        if allow_stale:
            stale = get_stale(url)
            if isinstance(stale, str):
                return stale
        raise exc
