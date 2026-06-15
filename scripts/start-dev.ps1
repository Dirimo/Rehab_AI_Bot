# Print commands to start RehabBot locally (3 terminals + Ollama)
$Root = Split-Path -Parent $PSScriptRoot

Write-Host @"

RehabBot — démarrage manuel (développement local)
=================================================

0) Ollama (si pas déjà lancé) :
   ollama serve
   ollama pull qwen3.5:9b-q4_K_M

1) Terminal MCP (port 8001) :
   cd "$Root\mcp-server"
   .\.venv\Scripts\python.exe run.py

2) Terminal Backend (port 8000) :
   cd "$Root\backend"
   .\.venv\Scripts\python.exe run.py

3) Terminal Frontend (port 3000) :
   cd "$Root\frontend"
   npm run dev

URLs :
   Frontend  → http://localhost:3000
   API docs  → http://localhost:8000/docs
   MCP       → http://localhost:8001/mcp

PostgreSQL : vérifiez DATABASE_URL dans backend/.env
   (Docker Compose : postgres:rehabbot@localhost:5432/rehabbot)

"@ -ForegroundColor Cyan
