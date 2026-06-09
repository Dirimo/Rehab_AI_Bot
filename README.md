# RehabBot — Assistant IA de Rééducation

**RehabBot** est un agent conversationnel intelligent dédié à la rééducation physique.
Il permet à un utilisateur (patient en rééducation, sportif amateur, étudiant) d'interagir en langage naturel avec un assistant capable de fournir des conseils généraux, de trouver des exercices depuis des sources publiques, et de rechercher des informations fiables en temps réel via scraping web.

> **Avertissement médical** : RehabBot est un outil pédagogique d'information et d'orientation.
> Il ne remplace pas un avis médical ni un suivi par un professionnel de santé.

---

## Stack technique

| Couche | Technologie | Rôle |
|--------|-------------|------|
| **Frontend** | Nuxt 3 / Vue.js (TypeScript) | Interface utilisateur, site vitrine, chatbot |
| **Backend** | Python / FastAPI | Orchestrateur : sessions, contexte, agent loop |
| **LLM Runtime** | Ollama (local) | Raisonnement, compréhension, génération de réponse |
| **Modèle** | Qwen3 1.7B / LLaMA 3.2 | Modèle open-source local |
| **Serveur MCP** | Python (FastMCP) | Exposition et exécution des tools de scraping |
| **Base de données** | PostgreSQL (prod) / SQLite (dev) | Sessions, messages, logs des appels tools |
| **Scraping** | BeautifulSoup / Zendriver | Extraction de données publiques en temps réel |

---

## Architecture

```
Navigateur (Nuxt 3)
    │
    ├── HTTP REST  ──────────────► FastAPI (port 8000)
    │   /sessions, /messages           │
    │                                  ├── SQLite / PostgreSQL
    └── WebSocket ───────────────►     │
        /ws/{session_id}               ├── Ollama (port 11434)
                                       │     └── Qwen3 1.7B / LLaMA 3.2
                                       │
                                       └── Serveur MCP (port 8001)
                                             ├── search_exercises
                                             ├── search_sources
                                             ├── get_rehab_advice
                                             └── scrape_article
```

---

## État d'avancement

### Membre 2 — Backend / Orchestration (FastAPI) ✅ TERMINÉ

**Fichiers livrés :**

| Fichier | Description |
|---------|-------------|
| `backend/app/main.py` | Point d'entrée FastAPI, CORS, lifespan |
| `backend/app/database.py` | Moteur async SQLModel, init BDD, purge sessions |
| `backend/app/models.py` | Tables : `sessions`, `messages`, `tool_logs` |
| `backend/app/routes/sessions.py` | CRUD sessions (POST/GET/DELETE) |
| `backend/app/routes/messages.py` | Envoi et historique des messages |
| `backend/app/mcp_client.py` | Client HTTP vers le serveur MCP + définition des tools |
| `backend/app/agent_loop.py` | Boucle IA : Ollama + tool_calls + réinjection contexte |
| `backend/app/websocket.py` | WebSocket `/ws/{session_id}` avec statuts temps réel |
| `backend/requirements.txt` | Dépendances Python |
| `backend/.env.example` | Variables d'environnement à copier |

**Routes REST disponibles :**

| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/sessions` | Créer une session |
| `GET` | `/sessions/{id}` | Récupérer une session (410 si expirée) |
| `GET` | `/sessions` | Lister toutes les sessions |
| `DELETE` | `/sessions/{id}` | Supprimer une session |
| `POST` | `/messages` | Envoyer un message (sans LLM) |
| `GET` | `/messages/{session_id}` | Historique de conversation |
| `GET` | `/health` | Santé de l'API |
| `WS` | `/ws/{session_id}` | WebSocket temps réel (chatbot) |

---

### Membre 4 — LLM / Prompts / Contexte (Ollama) ✅ TERMINÉ

**Fichiers livrés :**
| Fichier | Description |
|---------|-------------|
| `backend/app/agent_loop.py` | SYSTEM_PROMT finalisé + MAX_HISTORY_MESSAGE=40 |
| `backend/.env` | OLLAMA_MODEL=LLaMA3.2 configuré |
| `llm/model_comparison.md` | comparaison Qwen3 1.7B vs LLaMA3.2 + choix justifié  |
| `llm/system_prompt.md` | historique et versions du prompt système |
| `llm/test_questions.md` | jeu de questions de test + évaluation qualitative |

**Décisions techniques :**
| Décision | Valeur | Justification |
|---------|-------|-------------|
| Modèle retenu | `llama3.2` | Respect des garde-fous, français correct, anatomie sûre |
| Modèle écarté | `qwen3 1.7b` | Hallucitions dangereuses, dosages erronés, anatomie aberrante |
| `MAX_HISTORY_MESSAGES` | `40` | Fenêtre de contexte LLaMa 3.2 : 128K tokens |
| `MAX_TOOL_ITERATIONS` | `5` | Valeur par défaut conservée |


**Points d'intégration réalisés:**
- SYSTEM_PROMPT définit les conditions d'appel des tools vs réponse directe
- Garde-fous implémentés: refus dosages, refus diagnostic, redirection urgences vers le 15
- AVAILABLE_TOOLS dans mcp_client.py validé
  
---

### Membre 1 — Frontend / UX (Nuxt 3) ❌ À FAIRE

**Ce qui reste à faire :**
- [ ] Initialiser le projet Nuxt 3 avec TypeScript (`frontend/`)
- [ ] Page d'accueil (`/`) : présentation RehabBot, fonctionnalités, avertissement médical
- [ ] Page chatbot (`/chat`) : composant `ChatBot.vue` avec WebSocket
- [ ] Page à propos (`/about`)
- [ ] Layout Nuxt avec navigation
- [ ] Gestion de session côté client (localStorage `rehabbot_session_id`)
- [ ] Indicateurs visuels des statuts : `thinking`, `searching`, `réponse`
- [ ] Notification si session expirée (après 21 jours)
- [ ] Configurer `.env` : `NUXT_PUBLIC_API_BASE` et `NUXT_PUBLIC_WS_BASE`

**Points d'intégration avec le backend :**
- Créer une session : `POST http://localhost:8000/sessions`
- Charger l'historique : `GET http://localhost:8000/messages/{session_id}`
- Chat temps réel : WebSocket `ws://localhost:8000/ws/{session_id}`
- Format message WebSocket entrant : `{ "message": "texte" }`
- Voir les commentaires détaillés dans `backend/app/websocket.py` et `backend/app/routes/sessions.py`

---

### Membre 3 — MCP Server / Scraping (FastMCP) ❌ À FAIRE

**Ce qui reste à faire :**
- [ ] Initialiser le serveur FastMCP sur le port `8001` (`mcp_server/app/server.py`)
- [ ] Implémenter le tool `search_exercises(pathology: str)` — scraping sites kiné publics
- [ ] Implémenter le tool `search_sources(query: str)` — scraping HAS, Vidal, Ameli
- [ ] Implémenter le tool `get_rehab_advice(body_zone: str)` — sites médicaux publics
- [ ] Implémenter le tool `scrape_article(url: str)` — extraction article depuis URL
- [ ] Respecter `SCRAPING_RATE_LIMIT_SECONDS=2` entre les requêtes
- [ ] Rédiger `docs/architecture/mcp-tools.md`

**Contrat d'interface avec le backend :**
Le backend appelle `POST http://localhost:8001/tools/{tool_name}` avec le body JSON des arguments.

| Tool | Argument attendu | Exemple de réponse |
|------|------------------|--------------------|
| `search_exercises` | `{ "pathology": "tendinite" }` | `{ "exercises": [{ "title", "description", "source", "url" }] }` |
| `search_sources` | `{ "query": "lombalgie traitement" }` | `{ "sources": [{ "title", "content", "url" }] }` |
| `get_rehab_advice` | `{ "body_zone": "genou" }` | `{ "advice": [{ "title", "content", "url" }] }` |
| `scrape_article` | `{ "url": "https://..." }` | `{ "title", "content", "source", "url" }` |

En cas d'erreur, retourner : `{ "error": "description" }` (le backend gère ce cas proprement).
Voir le contrat complet dans les commentaires de `backend/app/mcp_client.py`.

---

### Membre 5 — DevOps / BDD / Documentation ❌ À FAIRE

**Ce qui reste à faire :**
- [ ] Écrire `backend/Dockerfile`
- [ ] Écrire `mcp_server/Dockerfile`
- [ ] Écrire `docker-compose.yml` (backend + MCP + base de données)
- [ ] Configurer les variables d'environnement dans Docker
- [ ] Tester la BDD en SQLite (dev) et PostgreSQL (prod)
- [ ] Mettre en place les migrations Alembic (le schéma est dans `backend/app/models.py`)
- [ ] Écrire `scripts/start.sh` et `scripts/health_check.sh`
- [ ] Maintenir `backend/.env.example` à jour
- [ ] Rédiger `docs/architecture/architecture-overview.md`
- [ ] Rédiger `docs/architecture/data-flow.md`
- [ ] Préparer `docs/presentation/soutenance-notes.md`

**Points d'intégration avec le backend :**
- Schéma BDD complet : `backend/app/models.py` (3 tables : `sessions`, `messages`, `tool_logs`)
- Purge des sessions expirées : `backend/app/database.py` → `purge_expired_sessions()`
- Variable DATABASE_URL : voir `backend/.env.example`
- CORS en prod : restreindre `allow_origins` dans `backend/app/main.py`

---

## Installation et démarrage

### Prérequis
- Python 3.11+
- Node.js 20+
- Ollama installé en local

### Backend (Membre 2 — disponible)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Éditer .env selon votre configuration
uvicorn app.main:app --reload --port 8000
```

Swagger disponible sur : http://localhost:8000/docs

### Frontend (Membre 1 — à venir)

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Serveur MCP (Membre 3 — à venir)

```bash
cd mcp_server
pip install -r requirements.txt
python app/server.py
```

### Ollama (Membre 4 — à configurer)

```bash
ollama serve
ollama pull qwen3:1.7b
```

---

## Variables d'environnement

Copier `backend/.env.example` vers `backend/.env` et adapter :

| Variable | Valeur par défaut | Description |
|----------|-------------------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./rehabbot.db` | URL de la base de données |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL du serveur Ollama |
| `OLLAMA_MODEL` | `qwen3:1.7b` | Modèle LLM à utiliser |
| `MCP_BASE_URL` | `http://localhost:8001` | URL du serveur MCP |
| `SESSION_EXPIRY_DAYS` | `21` | Durée de vie des sessions en jours |
| `APP_ENV` | `dev` | Environnement (dev / prod) |

---

## Planning

| Jour | Activités clés |
|------|----------------|
| J1 | Initialisation du repo, setup environnement, architecture validée en équipe |
| J2 | ✅ Backend : routes sessions + messages · MCP : structure du serveur · Frontend : layout de base |
| J3 | ✅ Backend : agent loop + intégration Ollama · LLM : premier prompt système |
| J4 | MCP : tools de scraping opérationnels · Frontend : interface chatbot + WebSocket |
| J5 | Intégration complète : frontend ↔ backend ↔ Ollama ↔ MCP |
| J6 | Tests end-to-end, corrections de bugs, amélioration des prompts |
| J7 | Finalisation documentation, préparation soutenance, démo finale |

---

## Règles de collaboration

- **Git** : une branche par fonctionnalité (`feature/frontend-chatbot`, `feature/mcp-scraping`, etc.)
- **Code review** : chaque PR doit être revue par au moins un autre membre avant merge
- **Point quotidien** : 15 minutes chaque matin pour synchroniser l'avancement
- **Intégration** : le Membre 5 est responsable de valider que tout fonctionne ensemble

---

*RehabBot — Prototype pédagogique open-source. Ne pas utiliser en contexte médical réel.*
