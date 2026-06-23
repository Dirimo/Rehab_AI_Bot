# Récupération de pages web avec cache et respect du robots.txt


import asyncio
import logging
import random
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from app.config import settings
from app.scraping.cache import get_cached, get_stale, set_cached
from app.scraping.content_validation import is_valid_medical_html
from app.scraping.firecrawl_client import scrape_markdown

logger = logging.getLogger(__name__)

# User-Agent pour simuler un navigateur réel (sinon httpx est souvent bloqué)
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

# API officielles : pas besoin de vérifier le robots.txt
API_HOSTS = frozenset(
    {
        "wsearch.nlm.nih.gov",
        "eutils.ncbi.nlm.nih.gov",
        "www.ncbi.nlm.nih.gov",
        "api.github.com",
        "raw.githubusercontent.com",
    }
)

_robots_cache: dict[str, RobotFileParser] = {}
_client: httpx.AsyncClient | None = None
_client_lock = asyncio.Lock()

# Per-domain rate limiting (fix #11)
_domain_locks: dict[str, asyncio.Lock] = {}
_last_request_by_domain: dict[str, float] = {}


def _domain_allowed(url):
    host = urlparse(url).netloc.lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in settings.ALLOWED_DOMAINS)


def _is_api_url(url):
    return urlparse(url).netloc.lower() in API_HOSTS


def _referer_for(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def _get_domain(url):
    return urlparse(url).netloc.lower()


async def _get_client():
    global _client
    async with _client_lock:
        if _client is None or _client.is_closed:
            _client = httpx.AsyncClient(
                timeout=30.0,
                headers=DEFAULT_HEADERS,
                follow_redirects=True,
                http2=True,
            )
        return _client


async def _respect_rate_limit(url):
    """Per-domain rate limiting — domains don't block each other."""
    domain = _get_domain(url)
    if domain not in _domain_locks:
        _domain_locks[domain] = asyncio.Lock()

    async with _domain_locks[domain]:
        base = settings.SCRAPING_RATE_LIMIT_SECONDS
        jitter = random.uniform(0, settings.SCRAPING_RATE_LIMIT_JITTER_SECONDS)
        last = _last_request_by_domain.get(domain, 0.0)
        wait_for = (base + jitter) - (time.monotonic() - last)
        if wait_for > 0:
            await asyncio.sleep(wait_for)
        _last_request_by_domain[domain] = time.monotonic()


async def _robots_allowed(url):
    """Check robots.txt asynchronously (non-blocking)."""
    if _is_api_url(url) or _domain_allowed(url):
        return True
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if base not in _robots_cache:
        parser = RobotFileParser()
        parser.set_url(f"{base}/robots.txt")
        try:
            client = await _get_client()
            resp = await client.get(f"{base}/robots.txt")
            parser.parse(resp.text.splitlines())
        except Exception:
            # If we can't fetch robots.txt, allow the request
            return True
        _robots_cache[base] = parser
    return _robots_cache[base].can_fetch(USER_AGENT, url)


async def _fetch_live(url):
    """Télécharge la page en direct."""
    if not _domain_allowed(url) and not _is_api_url(url):
        raise PermissionError(f"Domaine non autorisé pour le scraping : {url}")

    if not _is_api_url(url) and not await _robots_allowed(url):
        raise PermissionError(f"robots.txt interdit l'accès : {url}")

    await _respect_rate_limit(url)
    client = await _get_client()
    headers = {"Referer": _referer_for(url)}
    response = await client.get(url, headers=headers)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "pdf" in content_type.lower() or url.lower().endswith(".pdf"):
        return response.content, content_type
    return response.text, content_type


async def fetch_bytes(url, allow_stale=True):
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


async def fetch_html(url, allow_stale=True):
    """Récupère le contenu HTML avec cache local et Firecrawl."""
    cached = get_cached(url, settings.HTTP_CACHE_TTL_SECONDS)
    if isinstance(cached, str) and is_valid_medical_html(cached, url):
        return cached

    # Lazy Firecrawl fallback — fetched at most once (fix #13)
    firecrawl_result = None

    async def _try_firecrawl():
        nonlocal firecrawl_result
        if firecrawl_result is None:
            firecrawl_result = await scrape_markdown(url)
        return firecrawl_result

    try:
        body, content_type = await _fetch_live(url)
        if isinstance(body, bytes):
            if "pdf" in content_type.lower() or url.lower().endswith(".pdf"):
                raise ValueError("URL is a PDF; use fetch_bytes instead")
            text = body.decode("utf-8", errors="replace")
        else:
            text = body

        if is_valid_medical_html(text, url):
            set_cached(url, text)
            return text

        markdown = await _try_firecrawl()
        if markdown and is_valid_medical_html(markdown, url):
            set_cached(url, markdown)
            return markdown

        raise ValueError(f"Invalid or empty medical content from {url}")
    except Exception as exc:
        markdown = await _try_firecrawl()
        if markdown and is_valid_medical_html(markdown, url):
            set_cached(url, markdown)
            return markdown
        if allow_stale:
            stale = get_stale(url)
            if isinstance(stale, str) and is_valid_medical_html(stale, url):
                return stale
        raise exc
