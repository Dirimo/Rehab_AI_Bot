"""MedlinePlus official search API (NLM) — no HTML scraping required."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import httpx

from app.scraping.cache import get_cached, set_cached

_API_URL = "https://wsearch.nlm.nih.gov/ws/query"
_CACHE_TTL = 7 * 24 * 3600

# MedlinePlus search is English-first; map common French rehab terms.
_FR_TO_EN: dict[str, str] = {
    "dos": "back pain",
    "lombalgie": "low back pain exercises",
    "mal de dos": "back pain",
    "genou": "knee osteoarthritis exercises",
    "épaule": "shoulder pain exercises",
    "epaule": "shoulder pain exercises",
    "coiffe": "rotator cuff exercises",
    "hanche": "hip replacement exercises",
    "cheville": "ankle sprain exercises",
    "parkinson": "parkinson physical therapy",
    "tms": "musculoskeletal disorders",
    "arthrose": "osteoarthritis exercises",
}


def _english_query(term: str) -> str:
    key = term.strip().lower()
    return _FR_TO_EN.get(key, term)


def _strip_markup(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


async def search_health_topics(term: str, limit: int = 5) -> list[dict]:
    """Query MedlinePlus health topics; returns title, url, snippet, provider."""
    api_term = _english_query(term)
    cache_key = f"{_API_URL}?term={api_term}&limit={limit}"
    cached = get_cached(cache_key, _CACHE_TTL)
    if isinstance(cached, str):
        return _parse_response(cached, limit)

    params = {"db": "healthTopics", "term": api_term, "retmax": str(limit)}
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(_API_URL, params=params)
        response.raise_for_status()
        xml_text = response.text

    set_cached(cache_key, xml_text)
    return _parse_response(xml_text, limit)


def _parse_response(xml_text: str, limit: int) -> list[dict]:
    root = ET.fromstring(xml_text)
    items: list[dict] = []
    for doc in root.findall(".//document"):
        url = doc.attrib.get("url", "")
        title = ""
        snippet = ""
        org = "MedlinePlus (NIH)"
        for node in doc.findall("content"):
            name = node.attrib.get("name", "")
            text = _strip_markup("".join(node.itertext()))
            if name == "title" and text:
                title = text
            elif name == "snippet" and text:
                snippet = text
            elif name == "organizationName" and text:
                org = text
        if not title and url:
            title = url.rsplit("/", 1)[-1].replace(".html", "").replace("-", " ").title()
        if url:
            items.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet[:500],
                    "provider": org,
                }
            )
        if len(items) >= limit:
            break
    return items
