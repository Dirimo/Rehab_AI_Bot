# Présentation du Projet RehabBot - Répartition par Membre

Ce document détaille la structure recommandée pour la présentation de l'équipe. Le projet a été divisé de manière logique en 5 grands pôles, correspondant aux 5 membres de l'équipe (tels qu'identifiés dans l'architecture du code). Chaque membre dispose de 2 à 3 slides pour présenter son travail.

---

## Membre 1 : Frontend & Interface Utilisateur (Nuxt 3 / Vue.js)

**Rôle :** Responsable de l'interaction avec l'utilisateur, de l'ergonomie et de la communication avec l'API.

**Slide 1 : Architecture Frontend et Technologies**
- Présentation du choix de Nuxt 3 et Vue.js.
- Organisation du projet (composants, pages, composables).
- (Optionnel) Intégration de la 3D ou d'animations visuelles (utilisation de `three.js` présent dans les dépendances).

**Slide 2 : Expérience Utilisateur et Flux de Communication**
- Démonstration de l'interface de chat.
- Gestion de l'état en temps réel (affichage dynamique des statuts : *"thinking"*, *"searching"*, *"answer"*).
- Communication asynchrone avec le backend (endpoints REST et/ou WebSockets).

---

## Membre 2 : Backend & Base de Données (FastAPI / SQLModel)

**Rôle :** Responsable de l'orchestration, de l'API principale et de la persistance des données.

**Slide 1 : Architecture de l'API et Orchestration**
- Présentation de FastAPI comme point d'entrée central du système.
- Rôle du backend comme chef d'orchestre entre le frontend, le serveur MCP et le LLM.
- Gestion des routes, du middleware CORS et de l'asynchronisme.

**Slide 2 : Modélisation et Persistance (PostgreSQL)**
- Présentation du schéma de la base de données via `SQLModel`.
- Gestion des entités principales : Sessions utilisateurs, Messages et Logs d'outils (`ToolLog`).
- Traçabilité et historique des conversations pour garantir la mémoire de l'assistant.

---

## Membre 3 : Serveur MCP & Extraction de Données (FastMCP / Scraping)

**Rôle :** Fournisseur de compétences (outils) pour l'IA via le protocole MCP (recherche, scraping, traduction).

**Slide 1 : Le Protocole MCP (Model Context Protocol)**
- Qu'est-ce que MCP et pourquoi l'avoir utilisé ? (Standardisation de l'accès aux outils).
- Vue d'ensemble du serveur FastMCP.
- Présentation des outils exposés (`search_exercises`, `search_sources`, `get_rehab_advice`, `scrape_article`).

**Slide 2 : Scraping, Recherche et Traduction**
- Comment l'agent récupère de l'information fiable (Physiopedia, recommandations HAS/VIDAL).
- Utilisation de Firecrawl pour l'extraction de contenu d'articles.
- Le module de traduction asynchrone (utilisation locale d'Ollama) et son système d'optimisation par cache sécurisé (hachage SHA256).

---

## Membre 4 : Intelligence Artificielle & Agent Loop (Ollama / LLM)

**Rôle :** Cerveau du système, responsable du raisonnement logique et de l'intégration du modèle Qwen.

**Slide 1 : Choix du Modèle et Intégration Locale**
- L'utilisation d'Ollama et du modèle Qwen (ex: `qwen3.5:9b` ou `qwen2.5:7b`).
- Avantages du déploiement en local (confidentialité des données médicales, contrôle).
- Paramétrage de l'inférence (gestion du contexte, paramètres de prédiction).

**Slide 2 : La Boucle de l'Agent (Agent Loop / Pattern ReAct)**
- Explication du fichier `agent_loop.py`.
- Comment l'IA décide d'utiliser un outil (Raisonnement + Action).
- La boucle itérative : Réception de la question ➔ Choix de l'outil ➔ Exécution par le MCP ➔ Injection du résultat ➔ Synthèse finale.
- Les garde-fous mis en place (limitation des tours d'outils avec `AGENT_MAX_TOOL_ROUNDS` pour éviter les boucles infinies).

---

## Membre 5 : DevOps, Déploiement & Infrastructure (Docker)

**Rôle :** Responsable de l'intégration, de la conteneurisation et du lancement du projet.

**Slide 1 : Architecture de Déploiement**
- Présentation de la topologie avec Docker Compose.
- Les différents conteneurs et leurs interactions : Base de données (Postgres), Backend, Serveur MCP, et Frontend.
- L'utilisation du réseau Docker (ex: accès au LLM via `host.docker.internal`).

**Slide 2 : Gestion de la Configuration et Robustesse**
- Centralisation de la configuration (`config.py` et variables d'environnement via `.env`).
- Gestion des dépendances au démarrage (`depends_on` et scripts de `healthcheck` pour s'assurer que Postgres et le Backend sont prêts).
- Simplification du lancement pour les développeurs (`docker compose up --build`).
