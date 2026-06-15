"""
Serveur MCP — RehabBot
Membre 3 : MCP Server / Scraping

Expose 4 tools via HTTP POST sur le port 8001.
Le backend (mcp_client.py) appelle : POST /tools/{tool_name}

Lancement :
    pip install -r requirements_mcp.txt
    python server.py
"""



import asyncio
import os
import time

import httpx
import uvicorn
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

load_dotenv()

SCRAPING_RATE_LIMIT = float(os.getenv("SCRAPING_RATE_LIMIT_SECONDS", "2"))

app = FastAPI(
    title="RehabBot MCP Server",
    description="Serveur de tools de scraping pour RehabBot",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Schémas d'entrée — un par tool
# ---------------------------------------------------------------------------

class SearchExercisesInput(BaseModel):
    pathology: str  # ex: "tendinite rotulienne", "lombalgie"


class SearchSourcesInput(BaseModel):
    query: str  # ex: "rééducation genou ligament croisé"


class GetRehabAdviceInput(BaseModel):
    body_zone: str  # ex: "épaule", "genou", "dos"


class ScrapeArticleInput(BaseModel):
    url: str  # URL publique de l'article à extraire


# ---------------------------------------------------------------------------
# Utilitaires de scraping
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


async def _fetch_html(url: str, timeout: float = 10.0) -> str | None:
    """Récupère le HTML brut d'une page publique. Retourne None en cas d'erreur."""
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=HEADERS, follow_redirects=True) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.text
    except Exception:
        return None


def _extract_text(html: str, selector: str = "body") -> str:
    """Extrait le texte propre depuis le HTML via BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")
    # Suppression des balises inutiles
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    target = soup.select_one(selector) or soup.body or soup
    return " ".join(target.get_text(separator=" ").split())[:3000]  # max 3000 chars


# ---------------------------------------------------------------------------
# Tool 1 — search_exercises
# Sites cibles : kine-exercices.fr, exercices-kinesitherapie.fr (publics, sans auth)
# ---------------------------------------------------------------------------

EXERCISE_SOURCES = [
    "https://www.doctissimo.fr/html/sante/encyclopedie/sa_1040_reeducation.htm",
    "https://www.passeportsante.net/fr/Therapies/Guide/Fiche.aspx?doc=kinesitherapie_th&s={query}",
    "https://sante.lefigaro.fr/search?q={query}+exercice+rééducation",
]


@app.post("/tools/search_exercises")
async def search_exercises(body: SearchExercisesInput) -> JSONResponse:
    """
    Recherche des exercices de rééducation pour une pathologie donnée.
    Retourne une liste d'exercices avec titre, description, source et URL.
    """
    query = body.pathology.strip()
    exercises: list[dict] = []

    for url_template in EXERCISE_SOURCES:
        await asyncio.sleep(SCRAPING_RATE_LIMIT)
        url = url_template.format(query=query.replace(" ", "+"))
        html = await _fetch_html(url)
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")
        # Recherche générique : titres + paragraphes liés à la pathologie
        for tag in soup.find_all(["h2", "h3", "h4"])[:10]:
            title = tag.get_text(strip=True)
            if not title or len(title) < 5:
                continue
            # Description = paragraphe suivant (si disponible)
            description = ""
            sibling = tag.find_next_sibling(["p", "ul", "ol"])
            if sibling:
                description = sibling.get_text(separator=" ", strip=True)[:400]
            # Lien associé
            link = tag.find("a")
            exercise_url = link["href"] if link and link.get("href") else url

            exercises.append({
                "title": title,
                "description": description or "Voir la page source pour les détails.",
                "source": url.split("/")[2],
                "url": exercise_url,
            })

        if exercises:
            break  # On s'arrête au premier site qui donne des résultats

    if not exercises:
        return JSONResponse({"exercises": [], "info": f"Aucun exercice trouvé pour '{query}'."})

    return JSONResponse({"exercises": exercises[:6]})  # Max 6 résultats


# ---------------------------------------------------------------------------
# Tool 2 — search_sources
# Sites cibles : has-sante.fr, ameli.fr, vidal.fr (publics)
# ---------------------------------------------------------------------------

MEDICAL_SOURCES = [
    {"name": "HAS", "url": "https://www.has-sante.fr/recherche/?text={query}"},
    {"name": "Ameli", "url": "https://www.ameli.fr/assure/recherche?q={query}"},
    {"name": "Vidal", "url": "https://www.vidal.fr/recherche/?q={query}"},
]


@app.post("/tools/search_sources")
async def search_sources(body: SearchSourcesInput) -> JSONResponse:
    """
    Recherche des sources médicales fiables (HAS, Ameli, Vidal) sur un sujet.
    Retourne une liste de liens avec titre et extrait.
    """
    query = body.query.strip()
    sources: list[dict] = []

    for src in MEDICAL_SOURCES:
        await asyncio.sleep(SCRAPING_RATE_LIMIT)
        url = src["url"].format(query=query.replace(" ", "+"))
        html = await _fetch_html(url)
        if not html:
            sources.append({
                "site": src["name"],
                "url": url,
                "title": f"Résultats {src['name']} pour '{query}'",
                "excerpt": "Page non disponible au moment de la recherche.",
            })
            continue

        soup = BeautifulSoup(html, "html.parser")
        # Récupère les premiers résultats de recherche
        result_links = soup.select("a[href]")
        added = 0
        for a in result_links:
            href = a.get("href", "")
            title = a.get_text(strip=True)
            if not title or len(title) < 10:
                continue
            # Filtre : on garde les liens internes au domaine
            domain = src["url"].split("/")[2]
            if domain not in href and not href.startswith("/"):
                continue
            full_url = href if href.startswith("http") else f"https://{domain}{href}"
            sources.append({
                "site": src["name"],
                "url": full_url,
                "title": title[:150],
                "excerpt": "",
            })
            added += 1
            if added >= 2:
                break

        # Si aucun lien pertinent, on retourne la page de recherche directement
        if added == 0:
            sources.append({
                "site": src["name"],
                "url": url,
                "title": f"Recherche '{query}' sur {src['name']}",
                "excerpt": _extract_text(html)[:300] if html else "",
            })

    return JSONResponse({"sources": sources})


# ---------------------------------------------------------------------------
# Tool 3 — get_rehab_advice
# Conseils généraux par zone anatomique depuis des sites publics
# ---------------------------------------------------------------------------

ADVICE_SOURCES = {
    "épaule": "https://www.passeportsante.net/fr/Maux/Problemes/Fiche.aspx?doc=tendinite-epaule",
    "genou": "https://www.passeportsante.net/fr/Maux/Problemes/Fiche.aspx?doc=entorse-genou",
    "dos": "https://www.passeportsante.net/fr/Maux/Problemes/Fiche.aspx?doc=lombalgie",
    "cheville": "https://www.passeportsante.net/fr/Maux/Problemes/Fiche.aspx?doc=entorse-cheville",
    "poignet": "https://www.passeportsante.net/fr/Maux/Problemes/Fiche.aspx?doc=tendinite",
    "hanche": "https://www.passeportsante.net/fr/Maux/Problemes/Fiche.aspx?doc=coxarthrose",
    "nuque": "https://www.passeportsante.net/fr/Maux/Problemes/Fiche.aspx?doc=cervicalgie",
}

FALLBACK_ADVICE_URL = "https://www.passeportsante.net/fr/Therapies/Guide/Fiche.aspx?doc=kinesitherapie_th"

FALLBACK_ADVICE_URL = "https://www.ameli.fr/assure/sante/themes/reeducation"


@app.post("/tools/get_rehab_advice")
async def get_rehab_advice(body: GetRehabAdviceInput) -> JSONResponse:
    """
    Fournit des conseils généraux de rééducation pour une zone anatomique.
    Tente d'abord une URL ciblée, sinon scrape la page générale.
    """
    zone = body.body_zone.strip().lower()

    # Recherche d'une URL spécifique à la zone
    url = ADVICE_SOURCES.get(zone, FALLBACK_ADVICE_URL)

    await asyncio.sleep(SCRAPING_RATE_LIMIT)
    html = await _fetch_html(url)

    if not html:
        return JSONResponse({
            "body_zone": zone,
            "advice": [],
            "source": url,
            "error": "Page non disponible.",
        })

    soup = BeautifulSoup(html, "html.parser")
    advice_items: list[str] = []

    # Extraction des paragraphes et listes de conseils
    for tag in soup.select("p, li")[:30]:
        text = tag.get_text(strip=True)
        if len(text) > 40:  # filtre les textes trop courts (menus, etc.)
            advice_items.append(text[:300])
        if len(advice_items) >= 8:
            break

    if not advice_items:
        # Fallback : extraction brute du texte principal
        advice_items = [_extract_text(html)]

    return JSONResponse({
        "body_zone": zone,
        "advice": advice_items,
        "source": "Ameli.fr",
        "url": url,
    })


# ---------------------------------------------------------------------------
# Tool 4 — scrape_article
# Extraction du contenu d'un article depuis une URL fournie par le LLM
# ---------------------------------------------------------------------------

@app.post("/tools/scrape_article")
async def scrape_article(body: ScrapeArticleInput) -> JSONResponse:
    """
    Extrait le contenu textuel d'un article médical public depuis une URL.
    Ne fonctionne que sur des pages sans authentification ni CAPTCHA.
    """
    url = body.url.strip()

    # Validation basique de l'URL
    if not url.startswith("http"):
        return JSONResponse({"error": "URL invalide. Elle doit commencer par http:// ou https://"})

    await asyncio.sleep(SCRAPING_RATE_LIMIT)
    html = await _fetch_html(url)

    if not html:
        return JSONResponse({"error": f"Impossible de récupérer la page : {url}"})

    soup = BeautifulSoup(html, "html.parser")

    # Titre de l'article
    title_tag = soup.find("h1") or soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "Sans titre"

    # Contenu principal — on cible les balises sémantiques d'abord
    content = ""
    for selector in ["article", "main", ".content", ".article-body", "#content", "body"]:
        target = soup.select_one(selector)
        if target:
            for tag in target(["script", "style", "nav", "footer", "aside"]):
                tag.decompose()
            content = " ".join(target.get_text(separator=" ").split())[:3000]
            break

    # Domaine source
    source = url.split("/")[2] if len(url.split("/")) > 2 else url

    return JSONResponse({
        "title": title,
        "content": content,
        "source": source,
        "url": url,
    })


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "service": "RehabBot MCP Server"}


# ---------------------------------------------------------------------------
# Lancement
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("app.server:app", host="0.0.0.0", port=8001, reload=True)