"""Axomove scraper — illustrated exercises & therapeutic education (P2, French).

Axomove provides physiotherapy exercise content in French.  We target the
publicly accessible blog and exercise pages.  No translation needed.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup

from app.scraping.fetcher import fetch_html

logger = logging.getLogger(__name__)

_BASE = "https://www.axomove.com"

# Curated Axomove pages — public exercise/education content.
AXOMOVE_PAGES: dict[str, dict] = {
    "lombalgie": {
        "url": "https://www.axomove.com/axoblog/les-10-idees-recues-sur-le-mal-de-dos",
        "aliases": ("dos", "lombalgie", "mal de dos", "back"),
        "zone": "dos",
    },
    "cervicalgie": {
        "url": "https://www.axomove.com/axoblog/utiliser-votre-smartphone-est-il-responsable-de-vos-douleurs-au-cou",
        "aliases": ("cou", "cervicales", "cervicalgie", "neck", "nuque"),
        "zone": "cou",
    },
    "epaule": {
        "url": "https://www.axomove.com/axoblog/exercices-therapeutiques-anti-douleur-efficace-mouvement",
        "aliases": ("epaule", "épaule", "shoulder", "coiffe"),
        "zone": "epaule",
    },
    "genou": {
        "url": "https://www.axomove.com/axoblog/la-course-a-pied-cest-mauvais-pour-les-genoux",
        "aliases": ("genou", "knee", "arthrose genou"),
        "zone": "genou",
    },
    "hanche": {
        "url": "https://www.axomove.com/axoblog/exercices-therapeutiques-anti-douleur-efficace-mouvement",
        "aliases": ("hanche", "hip", "coxarthrose"),
        "zone": "hanche",
    },
    "cheville": {
        "url": "https://www.axomove.com/axoblog/conseil-de-kine-se-remettre-dune-blessure",
        "aliases": ("cheville", "ankle", "entorse"),
        "zone": "cheville",
    },
    "education_therapeutique": {
        "url": "https://www.axomove.com/axoblog/exercices-therapeutiques-anti-douleur-efficace-mouvement",
        "aliases": ("education therapeutique", "éducation thérapeutique", "etp"),
        "zone": "general",
    },
    "renforcement": {
        "url": "https://www.axomove.com/axoblog/les-10-idees-recues-sur-le-mal-de-dos",
        "aliases": ("renforcement", "musculation", "strengthening"),
        "zone": "general",
    },
}


def _match_axomove_pages(query: str, limit: int = 2) -> list[dict]:
    """Return curated Axomove pages whose aliases match the query."""
    q = query.strip().lower()
    if not q:
        return []

    hits: list[tuple[int, str, dict]] = []
    for key, page in AXOMOVE_PAGES.items():
        for alias in page["aliases"]:
            if alias in q:
                hits.append((len(alias), key, page))
                break

    hits.sort(key=lambda x: x[0], reverse=True)
    return [page for _, _, page in hits[:limit]]


def _extract_axomove_content(html: str, url: str) -> dict:
    """Extract exercise/education content from an Axomove blog page."""
    if html.lstrip().startswith("#") or ("## " in html and "<p>" not in html[:800]):
        lines = [ln.strip() for ln in html.splitlines() if ln.strip()]
        title = lines[0].lstrip("# ").strip() if lines else "Axomove"
        paragraphs = [re.sub(r"^#+\s*", "", ln) for ln in lines if len(ln) > 25]
        content = "\n".join(paragraphs)[:5000]
        return {
            "title": title,
            "url": url,
            "content": content,
            "provider": "Axomove",
            "lang": "fr",
        }

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
        tag.decompose()

    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    elif soup.title:
        title = soup.title.get_text(strip=True)

    # Axomove blog uses <article> or <main> for content
    main = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_="blog-content")
        or soup.find("div", class_="entry-content")
        or soup.body
    )

    paragraphs: list[str] = []
    if main:
        for node in main.find_all(["p", "h2", "h3", "li", "strong"]):
            text = " ".join(node.get_text(" ", strip=True).split())
            if len(text) > 25:
                if node.name in ("h2", "h3"):
                    paragraphs.append(f"\n## {text}")
                elif node.name == "li":
                    paragraphs.append(f"- {text}")
                else:
                    paragraphs.append(text)

    content = "\n".join(paragraphs)[:5000]

    return {
        "title": title or "Axomove",
        "url": url,
        "content": content,
        "provider": "Axomove",
        "lang": "fr",
    }


async def search_axomove_exercises(query: str, *, limit: int = 2) -> list[dict]:
    """Search curated Axomove pages for illustrated exercises."""
    results: list[dict] = []
    matched_pages = _match_axomove_pages(query, limit=limit)

    for page in matched_pages:
        try:
            html = await fetch_html(page["url"], allow_stale=True)
            article = _extract_axomove_content(html, page["url"])
            if article["content"]:
                article["zone"] = page.get("zone", "")
                results.append(article)
        except Exception as exc:
            logger.warning("Failed to fetch Axomove page %s: %s", page["url"], exc)
            continue

    return results
