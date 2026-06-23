# Fiche Technique : RehabBot

Ce document a pour but de donner une vue d'ensemble claire et approfondie du projet **RehabBot**. Il est indispensable que **chaque membre de l'équipe lise et comprenne cette fiche** afin d'avoir une vision globale du système, au-delà de sa propre partie, pour pouvoir répondre aux questions du jury lors de la soutenance.

---

## 1. Concept et Objectif
**RehabBot** est un prototype d'assistant virtuel spécialisé dans l'éducation à la rééducation (kinésithérapie).
**Attention :** Ce n'est pas un dispositif médical de diagnostic, mais un outil éducatif.
Pour garantir la confidentialité des données (très important dans le domaine médical), le projet s'appuie sur une Intelligence Artificielle **locale** (Ollama) plutôt que sur une API externe (comme ChatGPT).

---

## 2. Architecture Globale (Microservices)
Le projet est architecturé de manière moderne, autour de conteneurs Docker indépendants qui communiquent entre eux :

1. **Frontend (Nuxt 3 / Vue.js)** : L'interface utilisateur. Elle gère l'affichage interactif et envoie les requêtes HTTP au backend.
2. **Backend (FastAPI)** : Le "Chef d'Orchestre". Il ne génère pas de texte lui-même, mais il gère la base de données, l'historique des conversations, et transmet les messages entre le Frontend, le LLM et le Serveur MCP.
3. **Base de Données (PostgreSQL)** : Stocke les sessions utilisateurs, les messages de l'historique et les logs d'exécution des outils (pour la traçabilité).
4. **LLM local (Ollama / Qwen)** : Le "Cerveau". Hébergé directement sur la machine hôte. Il reçoit un contexte (historique), réfléchit, et peut demander l'utilisation d'outils.
5. **Serveur MCP (FastMCP)** : Le "Bras Armé". C'est un serveur indépendant qui contient les outils d'extraction d'information (recherche d'exercices, scraping de sites médicaux fiables type HAS, VIDAL).

---

## 3. Le Flux de Données (Comment ça marche de bout en bout ?)

Lorsqu'un utilisateur pose une question (ex: *"Quels exercices pour une entorse de la cheville ?"*) :

1. **Réception** : Le Frontend envoie la question au Backend.
2. **Sauvegarde & Contexte** : Le Backend enregistre la question en BDD, récupère les messages précédents de la session, et prépare un "Contexte" pour l'IA.
3. **Premier appel à l'IA (ReAct)** : Le Backend envoie le contexte au LLM (Ollama) en lui précisant : *"Voici les outils dont tu disposes"*.
4. **Décision de l'IA** : L'IA comprend qu'elle manque d'informations médicales à jour. Au lieu de répondre directement (et risquer d'halluciner), elle dit au Backend : *"Je veux utiliser l'outil `search_exercises` avec le paramètre `entorse cheville`"*.
5. **Exécution de l'outil (Serveur MCP)** : Le Backend contacte le Serveur MCP en lui demandant d'exécuter l'outil. Le Serveur MCP va chercher l'information (ex: via web scraping). S'il trouve des articles en anglais (Physiopedia), il utilise un mini-agent de traduction (Ollama) pour traduire le texte en français (mis en cache pour optimiser les performances).
6. **Deuxième appel à l'IA** : Le Serveur MCP renvoie le résultat (le texte des exercices) au Backend. Le Backend relance le LLM avec ce nouveau contexte : *"Voici ce que l'outil a trouvé : [...]"*.
7. **Synthèse et Réponse** : Le LLM lit le résultat, rédige une réponse finale claire et vulgarisée en français, et l'envoie au Backend.
8. **Clôture** : Le Backend sauvegarde la réponse en BDD et la renvoie au Frontend qui l'affiche à l'utilisateur.

---

## 4. Concepts Techniques Clés à Maîtriser pour le Jury

### A. Le Pattern ReAct (Reasoning and Acting)
C'est le concept central de l'IA moderne. Un modèle classique lit et répond. Un agent ReAct **réfléchit** ("J'ai besoin de chercher ça"), **agit** ("J'appelle l'outil de recherche"), **observe** ("Je lis le résultat de l'outil") et **répond**. Cela permet de réduire les hallucinations et de sourcer les informations.

### B. Le protocole MCP (Model Context Protocol)
Créé par Anthropic, ce protocole standardise la façon dont on donne des outils (compétences) à une IA. Au lieu de coder les outils directement dans le Backend (ce qui ferait un code monolithique et lourd), on les isole dans un Serveur MCP indépendant. Le Backend sert juste de "tuyau" entre le LLM et le Serveur MCP. Cela rend l'architecture ultra-scalable (on peut brancher d'autres serveurs MCP à l'avenir très facilement).

### C. L'Asynchronisme (async / await)
Dans le Backend et le Serveur MCP, tout est asynchrone (FastAPI, httpx, SQLAlchemy asynchrone avec psycopg).
**Pourquoi ?** Parce que les requêtes au LLM ou le scraping d'un site web prennent beaucoup de temps (plusieurs secondes). Si le code était bloquant (synchrone), le serveur serait gelé et ne pourrait pas répondre à un autre utilisateur pendant ce temps. L'asynchronisme permet au serveur de traiter d'autres requêtes en attendant la réponse de l'IA ou du site web.

### D. Confidentialité "Privacy by Design"
Grâce à l'utilisation de modèles Open Source hébergés localement via Ollama, aucune donnée médicale ou conversation utilisateur ne quitte le réseau privé vers des serveurs tiers (comme ceux d'OpenAI/Google). C'est un argument majeur pour une application de la santé.

---

## 5. Lexique Rapide
- **LLM** : Large Language Model (Modèle de langage, ici la famille Qwen).
- **Nuxt.js** : Framework basé sur Vue.js pour créer le frontend de manière performante.
- **FastAPI** : Framework Python moderne et rapide pour créer des API (Backend).
- **Docker Compose** : Outil permettant de lancer plusieurs conteneurs (Bdd, backend, frontend, mcp) via un seul fichier de configuration (`docker-compose.yml`).
- **SQLModel** : Librairie (mixant Pydantic et SQLAlchemy) qui permet de définir le format des tables de la base de données.
