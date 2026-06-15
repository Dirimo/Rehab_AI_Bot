# MCP tools — RehabBot (Member 3)

The MCP server exposes **four tools** over HTTP at `http://localhost:8001/mcp`.
The FastAPI backend (Member 2) calls them via `fastmcp.Client` during the agent loop.

## Architecture

```text
Backend (agent loop)
    │  fastmcp.Client.call_tool(name, args)
    ▼
MCP server (FastMCP)
    ├── search_exercises   → local bundle + curated pages (cache)
    ├── search_sources     → catalog + MedlinePlus API
    ├── get_rehab_advice   → one zone → article + exercise hints
    └── scrape_article     → single allowed URL (HTML or PDF)
```

## Tool reference

### `search_exercises(query: str)`

Recherche d'exercices de rééducation par pathologie ou zone anatomique.

**Sources (in order):**

1. **Bundle local** (`mcp-server/data/exercises_bundle.json`) — résumés offline (NHS, MedlinePlus). Toujours disponible, pas de scraping.
2. **Pages curatées** — entrées du catalogue `SOURCE_CATALOG` (HTML uniquement, pas les PDF), via cache HTTP 7 jours.

**Exemple de requête:** `"lombalgie"`, `"épaule"`, `"genou"`

**Réponse:** `{ query, items[], sources_used[], note? }`

---

### `search_sources(query: str)`

Recherche de sources fiables pour documentation ou citations.

**Sources:**

| Provider | Exemples |
|----------|----------|
| HAS | lombalgie, arthrose genou, coiffe des rotateurs |
| Santé publique France | TMS |
| MedlinePlus (NIH) | API officielle + fiches patient |
| NHS / CSP | exercices dos, épaule, physiotherapy |
| VIDAL | Parkinson (rééducation) |
| AP-HP / CHU | livrets PDF auto-rééducation |

**Réponse:** `{ query, sources: [{ title, url, provider, zone? }] }`

---

### `get_rehab_advice(body_zone: str)`

Conseils généraux pour une zone anatomique + exercices suggérés du bundle local.

**Zones / clés:** `dos`, `genou`, `epaule`, `cheville`, `hanche`, `cou`, ou alias du catalogue (`lombalgie`, `tms`, …).

**Réponse:** article structuré (`title`, `content`, `url`, `provider`) + `suggested_exercises[]`.

---

### `scrape_article(url: str)`

Extrait le contenu d'une URL **autorisée** (liste `ALLOWED_DOMAINS` dans `mcp-server/app/config.py`).

- **HTML** → BeautifulSoup (`extract_article`)
- **PDF** → pypdf (`extract_pdf_text`)

Respecte `robots.txt`, rate limiting (2 s + jitter), et cache disque.

---

## Source catalog

Défini dans `mcp-server/app/sources/registry.py` — **pas de crawling libre**, uniquement des URLs connues.

| Clé | Provider | Zone |
|-----|----------|------|
| `lombalgie` | HAS | dos |
| `genou` | HAS | genou |
| `epaule` | HAS | épaule |
| `apa` | HAS | — |
| `tms` | Santé publique France | épaule |
| `neuropathie` | AP-HP Bicêtre (PDF) | general |
| `membre_superieur` | CHU Montpellier (PDF) | épaule |
| `rotator_cuff` | MedlinePlus | épaule |
| `hip_replacement` | MedlinePlus | hanche |
| `back_pain_topic` | MedlinePlus | dos |
| `nhs_back_exercises` | NHS | dos |
| `nhs_shoulder` | NHS | épaule |
| `nhs_physio` | NHS | — |
| `csp_msk` | CSP | — |
| `csp_exercises` | CSP | — |
| `parkinson` | VIDAL | general |

Le matching se fait par **alias** contenus dans la requête (`match_sources`).

## Safety & compliance

- **Allowlist de domaines** — seules les URLs des institutions listées sont fetchées.
- **robots.txt** — vérifié avant chaque requête HTTP distante.
- **Rate limiting** — délai configurable (`SCRAPING_RATE_LIMIT_SECONDS`, défaut 2 s).
- **Cache** — `mcp-server/.cache/` (TTL 7 jours) pour limiter la charge sur les sites sources.
- **Ameli.fr** — souvent bloqué dans robots.txt ; le catalogue privilégie HAS, NHS et MedlinePlus.

## Ollama tool schemas (Member 2)

Les descriptions exposées au LLM sont dans `backend/app/services/mcp_client.py` (`OLLAMA_TOOLS`).
Elles doivent rester alignées avec le comportement réel des outils MCP.

## Run locally

```powershell
cd mcp-server
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
# → http://localhost:8001/mcp
```

Via Docker : service `mcp-server` dans `docker compose up`.
