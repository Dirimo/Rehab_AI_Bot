"""PubMed Central (PMC) search via NCBI E-utilities API (P2, English).

Uses the official NCBI E-utilities (esearch + efetch) — no HTML scraping.
Returns article titles, abstracts, and PMC URLs.  Abstracts are translated
EN → FR via the local Ollama translator.

API docs: https://www.ncbi.nlm.nih.gov/books/NBK25499/
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import httpx

from app.scraping.cache import get_cached, set_cached
from app.scraping.translator import translate_en_to_fr

logger = logging.getLogger(__name__)

_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
_CACHE_TTL = 7 * 24 * 3600  # 7 days

# Map common French rehab terms to English PubMed queries.
_FR_TO_EN: dict[str, str] = {
    "dos": "low back pain rehabilitation exercises",
    "lombalgie": "chronic low back pain physiotherapy",
    "mal de dos": "back pain rehabilitation",
    "genou": "knee osteoarthritis physiotherapy rehabilitation",
    "épaule": "shoulder rehabilitation exercises physiotherapy",
    "epaule": "shoulder rehabilitation exercises physiotherapy",
    "coiffe": "rotator cuff rehabilitation exercises",
    "hanche": "hip replacement rehabilitation physiotherapy",
    "cheville": "ankle sprain rehabilitation exercises",
    "parkinson": "parkinson disease physical therapy rehabilitation",
    "arthrose": "osteoarthritis physiotherapy exercise",
    "cervicales": "cervical pain physiotherapy exercises",
    "tms": "musculoskeletal disorders rehabilitation",
    "sciatique": "sciatica physiotherapy treatment",
    "tendinite": "tendinitis rehabilitation exercises",
    "prothese": "joint replacement rehabilitation",
    "avc": "stroke rehabilitation physiotherapy",
}


def _english_query(term: str) -> str:
    """Convert a French term to an English PubMed search query."""
    key = term.strip().lower()
    return _FR_TO_EN.get(key, f"{term} rehabilitation physiotherapy")


async def search_pmc_articles(
    query: str, *, limit: int = 3, translate: bool = True
) -> list[dict]:
    """Search PubMed Central for rehabilitation-related scientific articles.

    Returns a list of dicts with: title, abstract, url, authors, provider.
    Abstracts are translated to French by default.
    """
    en_query = _english_query(query)
    cache_key = f"pmc:search:{en_query}:{limit}"

    # Check cache for the full result set
    cached = get_cached(cache_key, _CACHE_TTL)
    if isinstance(cached, str):
        import json
        try:
            return json.loads(cached)
        except Exception:
            pass

    try:
        # Step 1: esearch — get PMC IDs
        pmc_ids = await _esearch(en_query, limit=limit)
        if not pmc_ids:
            return []

        # Step 2: efetch — get article details
        articles = await _efetch(pmc_ids)

        # Step 3: translate abstracts EN → FR
        if translate:
            for article in articles:
                if article.get("abstract"):
                    article["abstract_original"] = article["abstract"]
                    article["abstract"] = await translate_en_to_fr(article["abstract"])
                if article.get("title"):
                    article["title_original"] = article["title"]
                    article["title"] = await translate_en_to_fr(article["title"])
                article["lang"] = "fr (traduit)"

        # Cache the results
        import json
        set_cached(cache_key, json.dumps(articles, ensure_ascii=False))

        return articles

    except Exception as exc:
        logger.warning("PMC search failed for '%s': %s", query, exc)
        return []


async def _esearch(query: str, limit: int = 3) -> list[str]:
    """Search PubMed Central and return PMC IDs."""
    params = {
        "db": "pmc",
        "term": f"{query} AND open access[filter]",
        "retmax": str(limit),
        "retmode": "json",
        "sort": "relevance",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(_ESEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json()

    id_list = data.get("esearchresult", {}).get("idlist", [])
    return id_list[:limit]


async def _efetch(pmc_ids: list[str]) -> list[dict]:
    """Fetch article details from PMC by IDs."""
    if not pmc_ids:
        return []

    params = {
        "db": "pmc",
        "id": ",".join(pmc_ids),
        "retmode": "xml",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(_EFETCH_URL, params=params)
        response.raise_for_status()
        xml_text = response.text

    return _parse_pmc_xml(xml_text)


def _parse_pmc_xml(xml_text: str) -> list[dict]:
    """Parse PMC efetch XML response into structured article dicts."""
    articles: list[dict] = []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        logger.warning("Failed to parse PMC XML response")
        return []

    for article_el in root.findall(".//article"):
        try:
            # Title
            title_el = article_el.find(".//article-title")
            title = ""
            if title_el is not None:
                title = "".join(title_el.itertext()).strip()

            # Abstract
            abstract_parts: list[str] = []
            for abs_el in article_el.findall(".//abstract//p"):
                text = "".join(abs_el.itertext()).strip()
                if text:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts)

            # If no structured abstract, try the full abstract text
            if not abstract:
                abs_el = article_el.find(".//abstract")
                if abs_el is not None:
                    abstract = "".join(abs_el.itertext()).strip()

            # Authors
            authors: list[str] = []
            for contrib in article_el.findall(".//contrib[@contrib-type='author']"):
                surname = contrib.findtext("name/surname", "")
                given = contrib.findtext("name/given-names", "")
                if surname:
                    authors.append(f"{given} {surname}".strip())

            # PMC ID for URL
            pmc_id = ""
            for art_id in article_el.findall(".//article-id"):
                if art_id.get("pub-id-type") == "pmc":
                    pmc_id = art_id.text or ""
                    break

            # DOI
            doi = ""
            for art_id in article_el.findall(".//article-id"):
                if art_id.get("pub-id-type") == "doi":
                    doi = art_id.text or ""
                    break

            url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/" if pmc_id else ""

            if title or abstract:
                articles.append({
                    "title": title or "Article PMC",
                    "abstract": abstract[:3000] if abstract else "",
                    "content": abstract[:3000] if abstract else "",
                    "authors": ", ".join(authors[:5]),
                    "doi": doi,
                    "url": url,
                    "provider": "PMC (PubMed Central)",
                    "lang": "en",
                })

        except Exception as exc:
            logger.warning("Failed to parse a PMC article: %s", exc)
            continue

    return articles
