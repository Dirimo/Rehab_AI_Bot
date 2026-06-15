# RehabBot — scripts utilitaires (Member 5)

## Développement local (sans Docker)

### Windows — `setup-dev.ps1`

Crée les venv Python, installe les dépendances, copie les fichiers `.env` depuis les templates.

```powershell
.\scripts\setup-dev.ps1
```

### Windows — `start-dev.ps1`

Affiche les commandes à lancer dans **3 terminaux** (MCP, backend, frontend) + rappel Ollama.

```powershell
.\scripts\start-dev.ps1
```

## Docker (stack complète sauf Ollama)

Ollama doit tourner sur la machine hôte avec le modèle chargé :

```powershell
ollama pull qwen3.5:9b-q4_K_M
ollama serve
```

Puis :

```powershell
.\scripts\docker-up.ps1
```

Services :

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/docs |
| MCP | http://localhost:8001/mcp |
| PostgreSQL | localhost:5432 (user `postgres`, password `rehabbot`, db `rehabbot`) |

## Vérification rapide

```powershell
.\scripts\health-check.ps1
```

Teste `/health` du backend et la disponibilité du port MCP.
