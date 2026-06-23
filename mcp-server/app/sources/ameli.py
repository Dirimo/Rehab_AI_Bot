# Scraper pour Ameli.fr - Infos de rééducation


import logging
import re
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup

from app.scraping.fetcher import fetch_html

logger = logging.getLogger(__name__)

_BASE = "https://www.ameli.fr"

# Pages présélectionnées d'Ameli par zone ou pathologie
AMELI_PAGES = {
    "lombalgie": {
        "url": "https://www.ameli.fr/assure/sante/themes/lombalgie-aigue/comprendre-lombalgie",
        "aliases": ("dos", "lombalgie", "mal de dos", "back"),
        "zone": "dos",
    },
    "lombalgie_traitement": {
        "url": "https://www.ameli.fr/assure/sante/themes/lombalgie-aigue/traitement-prevention",
        "aliases": ("traitement dos", "soigner lombalgie"),
        "zone": "dos",
    },
    "genou": {
        "url": "https://www.ameli.fr/assure/sante/themes/arthrose-genou/definition-facteurs-favorisants",
        "aliases": ("genou", "arthrose genou", "gonarthrose"),
        "zone": "genou",
    },
    "epaule": {
        "url": "https://www.ameli.fr/assure/sante/themes/epaule-douloureuse/definition-causes-facteurs-favorisants",
        "aliases": ("epaule", "épaule", "tendinite épaule", "shoulder"),
        "zone": "epaule",
    },
    "cheville": {
        "url": "https://www.ameli.fr/assure/sante/themes/entorse-cheville/consultation-traitement",
        "aliases": ("cheville", "entorse", "ankle"),
        "zone": "cheville",
    },
    "hanche": {
        "url": "https://www.ameli.fr/assure/sante/themes/arthrose-hanche/definition-facteurs-favorisants",
        "aliases": ("hanche", "coxarthrose", "hip"),
        "zone": "hanche",
    },
    "kinesitherapie": {
        "url": "https://www.ameli.fr/assure/remboursements/rembourse/consultation-sages-femmes-auxiliaires-medicaux/kinesitherapie",
        "aliases": ("kinesitherapie", "kinésithérapie", "remboursement", "kiné", "prise en charge"),
        "zone": "general",
    },
    "arret_travail": {
        "url": "https://www.ameli.fr/assure/droits-demarches/maladie-accident-hospitalisation/arret-maladie/arret-travail",
        "aliases": ("arret travail", "arrêt maladie", "indemnités"),
        "zone": "general",
    },
}


def _match_ameli_pages(query, limit=2):
    """Trouve les pages Ameli qui correspondent à la recherche."""
    q = query.strip().lower()
    if not q:
        return []

    hits: list[tuple[int, str, dict]] = []
    for key, page in AMELI_PAGES.items():
        for alias in page["aliases"]:
            if alias in q:
                hits.append((len(alias), key, page))
                break

    hits.sort(key=lambda x: x[0], reverse=True)
    return [page for _, _, page in hits[:limit]]


def _extract_ameli_content(html, url):
    """Extrait le texte d'une page HTML d'Ameli.fr."""
    if html.lstrip().startswith("#") or ("## " in html and "<p>" not in html[:800]):
        lines = [ln.strip() for ln in html.splitlines() if ln.strip()]
        title = lines[0].lstrip("# ").strip() if lines else "Ameli.fr"
        paragraphs = [re.sub(r"^#+\s*", "", ln) for ln in lines if len(ln) > 30]
        content = "\n".join(paragraphs)[:5000]
        return {
            "title": title or "Ameli.fr",
            "url": url,
            "content": content,
            "provider": "Ameli.fr",
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

    # Ameli utilise <main> ou <article> pour son contenu principal
    main = soup.find("main") or soup.find("article") or soup.find("div", class_="article-content") or soup.body

    paragraphs: list[str] = []
    if main:
        for node in main.find_all(["p", "h2", "h3", "li"]):
            text = " ".join(node.get_text(" ", strip=True).split())
            if len(text) > 30:
                if node.name in ("h2", "h3"):
                    paragraphs.append(f"\n## {text}")
                elif node.name == "li":
                    paragraphs.append(f"- {text}")
                else:
                    paragraphs.append(text)

    content = "\n".join(paragraphs)[:5000]

    return {
        "title": title or "Ameli.fr",
        "url": url,
        "content": content,
        "provider": "Ameli.fr",
        "lang": "fr",
    }


async def search_ameli(query, limit=2):
    """Recherche des pages Ameli correspondantes."""
    results = []
    matched_pages = _match_ameli_pages(query, limit=limit)

    for page in matched_pages:
        try:
            html = await fetch_html(page["url"], allow_stale=True)
            article = _extract_ameli_content(html, page["url"])
            if article["content"]:
                article["zone"] = page.get("zone", "")
                results.append(article)
        except Exception as exc:
            logger.warning("Failed to fetch Ameli page %s: %s", page["url"], exc)
            continue

    return results


async def get_ameli_advice(body_zone):
    """Récupère les conseils d'Ameli pour une zone spécifique."""
    pages = _match_ameli_pages(body_zone, limit=1)
    if not pages:
        return None

    page = pages[0]
    try:
        html = await fetch_html(page["url"], allow_stale=True)
        article = _extract_ameli_content(html, page["url"])
        article["zone"] = page.get("zone", "")
        return article
    except Exception as exc:
        logger.warning("Failed to fetch Ameli advice for '%s': %s", body_zone, exc)
        return None
