"""Physiopedia scraper — structured rehabilitation exercises (P0, English).

Physiopedia wiki lives at physio-pedia.com (hyphenated domain).  We use curated
article URLs and MediaWiki search, then parse exercise / rehabilitation sections.

All returned content is translated EN → FR via the local Ollama translator.
"""

from __future__ import annotations

import logging
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup

from app.scraping.fetcher import fetch_html
from app.scraping.translator import translate_en_to_fr

logger = logging.getLogger(__name__)

_BASE = "https://www.physio-pedia.com"
_SEARCH_URL = _BASE + "/index.php?search={query}&title=Special%3ASearch&fulltext=1"

# Curated articles validated via Firecrawl (old physiopedia.com domain is parked).
CURATED_ARTICLES: dict[str, str] = {
    "dos": f"{_BASE}/Low_Back_Pain",
    "lombalgie": f"{_BASE}/Low_Back_Pain",
    "mal de dos": f"{_BASE}/Low_Back_Pain",
    "back": f"{_BASE}/Low_Back_Pain",
    "genou": f"{_BASE}/Knee_Osteoarthritis",
    "arthrose genou": f"{_BASE}/Knee_Osteoarthritis",
    "epaule": f"{_BASE}/Rotator_Cuff_Tendinopathy",
    "épaule": f"{_BASE}/Rotator_Cuff_Tendinopathy",
    "coiffe": f"{_BASE}/Rotator_Cuff_Tendinopathy",
    "cheville": f"{_BASE}/Ankle_Sprain",
    "entorse": f"{_BASE}/Ankle_Sprain",
    "cervicales": f"{_BASE}/Neck_Pain",
    "cou": f"{_BASE}/Neck_Pain",
    "hanche": f"{_BASE}/Hip_Osteoarthritis",
    "parkinson": f"{_BASE}/Parkinson%27s_Disease",
    "avc": f"{_BASE}/Stroke",
}


def _build_search_url(query: str) -> str:
    return _SEARCH_URL.format(query=quote_plus(query))


def _extract_search_links(html: str, limit: int = 3) -> list[dict]:
    """Parse Physiopedia search results page and return article links."""
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict] = []

    for div in soup.select(".mw-search-result-heading a, .searchresult a"):
        href = div.get("href", "")
        title = div.get_text(strip=True)
        if not href or not title or len(title) < 5:
            continue
        full_url = urljoin(_BASE, href)
        if "physio-pedia.com" not in full_url and "physiopedia.com" not in full_url:
            continue
        results.append({"title": title, "url": full_url})
        if len(results) >= limit:
            break

    if not results:
        search_area = soup.find("div", class_="searchresults") or soup.find("div", id="mw-content-text") or soup
        for link in search_area.find_all("a", href=True):
            href = link["href"]
            title = link.get_text(strip=True)
            if (
                href.startswith("/")
                and not href.startswith("/index.php")
                and not href.startswith("/Special:")
                and len(title) > 10
            ):
                full_url = urljoin(_BASE, href)
                results.append({"title": title, "url": full_url})
                if len(results) >= limit:
                    break

    return results


def _extract_exercise_sections(html: str, url: str) -> dict:
    """Extract rehabilitation/exercise content from a Physiopedia article."""
    # Firecrawl may return markdown instead of HTML.
    if html.lstrip().startswith("#") or ("## " in html and "<p>" not in html[:500]):
        lines = [ln.strip() for ln in html.splitlines() if ln.strip()]
        content = "\n".join(lines)[:5000]
        title = lines[0].lstrip("# ").strip() if lines else "Physiopedia Article"
        return {
            "title": title,
            "url": url,
            "content": content,
            "provider": "Physiopedia",
            "lang": "en",
        }

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "noscript"]):
        tag.decompose()

    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    elif soup.title:
        title = soup.title.get_text(strip=True)

    target_keywords = [
        "exercise", "rehabilitation", "management", "treatment",
        "physiotherapy", "physical therapy", "intervention",
        "stretching", "strengthening", "program",
    ]

    content_parts: list[str] = []
    main = soup.find("div", id="mw-content-text") or soup.find("main") or soup.find("article") or soup.body

    if main:
        current_section_relevant = False
        for element in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "ol", "ul"]):
            if element.name in ("h1", "h2", "h3", "h4"):
                heading_text = element.get_text(strip=True).lower()
                current_section_relevant = any(kw in heading_text for kw in target_keywords)
                if current_section_relevant:
                    content_parts.append(f"\n## {element.get_text(strip=True)}")
            elif current_section_relevant:
                text = " ".join(element.get_text(" ", strip=True).split())
                if len(text) > 30:
                    if element.name == "li":
                        content_parts.append(f"- {text}")
                    else:
                        content_parts.append(text)

        if not content_parts:
            for p in main.find_all(["p", "li"]):
                text = " ".join(p.get_text(" ", strip=True).split())
                if len(text) > 40:
                    content_parts.append(text)

    content = "\n".join(content_parts)[:5000]

    return {
        "title": title or "Physiopedia Article",
        "url": url,
        "content": content,
        "provider": "Physiopedia",
        "lang": "en",
    }


from app.sources.pmc import _FR_TO_EN


def _curated_urls(query: str, limit: int) -> list[dict]:
    """Return known-good Physiopedia URLs for common French rehab terms."""
    q = query.strip().lower()
    hits: list[tuple[int, str]] = []
    for alias, article_url in CURATED_ARTICLES.items():
        if alias in q:
            hits.append((len(alias), article_url))
    hits.sort(key=lambda item: item[0], reverse=True)

    seen: set[str] = set()
    links: list[dict] = []
    for _, article_url in hits:
        if article_url in seen:
            continue
        seen.add(article_url)
        slug = article_url.rsplit("/", 1)[-1].replace("_", " ")
        links.append({"title": slug, "url": article_url})
        if len(links) >= limit:
            break
    return links


async def search_physiopedia_exercises(
    query: str, *, limit: int = 2, translate: bool = True
) -> list[dict]:
    """Search Physiopedia for rehabilitation exercises.

    Returns a list of structured exercise/article dicts, translated to French.
    """
    results: list[dict] = []

    key = query.strip().lower()
    en_query = _FR_TO_EN.get(key, query)

    links = _curated_urls(query, limit=limit)
    if not links:
        try:
            search_url = _build_search_url(en_query)
            search_html = await fetch_html(search_url, allow_stale=True)
            links = _extract_search_links(search_html, limit=limit)
        except Exception as exc:
            logger.warning("Physiopedia search failed for '%s': %s", query, exc)
            return []

    for link_info in links:
        try:
            article_html = await fetch_html(link_info["url"], allow_stale=True)
            article = _extract_exercise_sections(article_html, link_info["url"])

            if not article["content"] or len(article["content"]) < 200:
                continue

            if translate and article.get("lang") == "en":
                article["title"] = await translate_en_to_fr(article["title"])
                article["content"] = await translate_en_to_fr(article["content"])
                article["lang"] = "fr (traduit)"

            results.append(article)
        except Exception as exc:
            logger.warning("Failed to fetch Physiopedia article %s: %s", link_info["url"], exc)
            continue

    return results
