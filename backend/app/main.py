"""RehabBot backend entrypoint (Member 2 — FastAPI orchestrator).

Run locally (from the `backend/` folder, with the venv active):
    uvicorn app.main:app --reload --port 8000

Interactive API docs are then available at:  http://localhost:8000/docs
"""

import asyncio
import sys
from contextlib import asynccontextmanager

# Windows-only fix: psycopg's async mode cannot run on the default
# ProactorEventLoop. We must select the SelectorEventLoop policy BEFORE the
# event loop is created (i.e. at import time, before uvicorn starts the loop).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import async_session_maker, init_db
from app.routers import chat, messages, sessions, ws
from app.routers.sessions import purge_expired_sessions


import logging
logger = logging.getLogger(__name__)

async def _purge_loop():
    """Background task to periodically purge expired sessions."""
    while True:
        try:
            async with async_session_maker() as db:
                count = await purge_expired_sessions(db)
                if count > 0:
                    logger.info("Purged %d expired sessions.", count)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("Failed to purge sessions: %s", exc)
        # Sleep for 1 hour
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    # Create database tables if they don't exist yet.
    await init_db()
    
    # Start the background purge loop
    purge_task = asyncio.create_task(_purge_loop())
    
    yield
    
    # --- shutdown ---
    purge_task.cancel()
    try:
        await purge_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="RehabBot API",
    description="Orchestrates the chat flow between the frontend, the LLM, and the MCP server.",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow the Nuxt frontend (a different origin) to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(messages.router)
app.include_router(chat.router)
app.include_router(ws.router)


@app.get("/health", tags=["system"])
async def health() -> dict:
    """Lightweight liveness check used by tooling and Member 5's scripts."""
    return {"status": "ok"}
