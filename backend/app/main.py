"""
Point d'entrée de l'API FastAPI — RehabBot Backend

► TOUS LES MEMBRES :
    Swagger UI (documentation interactive) : http://localhost:8000/docs
    Santé de l'API                         : http://localhost:8000/health

    Lancement en développement :
        cd backend
        pip install -r requirements.txt
        cp .env.example .env      # puis éditer .env selon votre config
        uvicorn app.main:app --reload --port 8000

► MEMBRE 5 (DevOps / Docker) :
    - Le lifespan gère l'initialisation de la BDD et la purge des sessions expirées au démarrage.
    - Pour le Dockerfile, le CMD sera :
        CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    - CORS est actuellement ouvert (allow_origins=["*"]).
      En prod, restreins allow_origins à l'URL du frontend Nuxt.

► MEMBRE 1 (Frontend / UX) :
    - API base URL : NUXT_PUBLIC_API_BASE=http://localhost:8000
    - WebSocket base URL : NUXT_PUBLIC_WS_BASE=ws://localhost:8000
    - Toutes les routes sont documentées sur /docs.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db, purge_expired_sessions
from app.routes import sessions, messages
from app import websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await purge_expired_sessions()
    yield


app = FastAPI(
    title="RehabBot API",
    description="Backend API pour l'assistant IA de rééducation RehabBot",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ► MEMBRE 5 : restreindre en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(messages.router)
app.include_router(websocket.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
