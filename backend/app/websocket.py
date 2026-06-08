"""
Endpoint WebSocket — /ws/{session_id}

C'est le canal de communication temps réel entre le frontend et le backend.
Toute la conversation passe par ici (pas par les routes REST).

► MEMBRE 1 (Frontend / UX) :
    URL de connexion : ws://localhost:8000/ws/{session_id}
    En prod       : wss://{domaine}/ws/{session_id}
    Variable d'environnement Nuxt : NUXT_PUBLIC_WS_BASE=ws://localhost:8000

    Protocole WebSocket côté client :

    1. Connexion :
       Le backend envoie immédiatement après connexion :
         { "type": "connected", "session_id": "uuid" }
       Si la session est expirée ou introuvable :
         { "type": "error", "code": "SESSION_EXPIRED", "message": "..." }
         → Le WebSocket est fermé avec le code 4410.
         → Côté client : créer une nouvelle session via POST /sessions puis reconnecter.

    2. Envoyer un message utilisateur :
       ws.send(JSON.stringify({ "message": "texte du message" }))

    3. Recevoir les événements du backend (dans l'ordre) :
       a) Statuts intermédiaires (0 à N fois) :
            { "type": "status", "status": "thinking", "label": "Analyse de votre message…" }
            { "type": "status", "status": "searching", "label": "Recherche via search_exercises…" }
            { "type": "status", "status": "thinking", "label": "Formulation de la réponse…" }
          → Afficher ces statuts comme indicateur visuel (spinner + label).

       b) Réponse finale (1 fois) :
            { "type": "message", "role": "assistant", "content": "texte de la réponse" }
          → Ajouter ce message dans le fil de conversation.

    4. Gestion des erreurs :
         { "type": "error", "code": "EMPTY_MESSAGE" | "INVALID_JSON" | "INTERNAL_ERROR", "message": "..." }

    Exemple d'implémentation Vue.js :
        const ws = new WebSocket(`${wsBase}/ws/${sessionId}`)
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data)
          if (data.type === 'status') showStatus(data.label)
          if (data.type === 'message') addMessage(data)
          if (data.type === 'error' && data.code === 'SESSION_EXPIRED') handleExpiredSession()
        }
        ws.send(JSON.stringify({ message: userInput }))
"""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlmodel import select

from app.database import AsyncSessionLocal
from app.models import Session
from app.agent_loop import run_agent

router = APIRouter(tags=["websocket"])


async def _send(ws: WebSocket, payload: dict) -> None:
    await ws.send_text(json.dumps(payload, ensure_ascii=False))


async def _check_session(session_id: str, db) -> bool:
    result = await db.exec(select(Session).where(Session.id == session_id))
    session = result.first()
    if not session:
        return False
    now = datetime.now(timezone.utc)
    expires = session.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return expires >= now


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(ws: WebSocket, session_id: str):
    await ws.accept()

    async with AsyncSessionLocal() as db:
        if not await _check_session(session_id, db):
            await _send(ws, {
                "type": "error",
                "code": "SESSION_EXPIRED",
                "message": "Session expirée ou introuvable.",
            })
            await ws.close(code=4410)
            return

        await _send(ws, {"type": "connected", "session_id": session_id})

        try:
            while True:
                raw = await ws.receive_text()

                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    await _send(ws, {"type": "error", "code": "INVALID_JSON", "message": "Message invalide."})
                    continue

                user_message = data.get("message", "").strip()
                if not user_message:
                    await _send(ws, {"type": "error", "code": "EMPTY_MESSAGE", "message": "Message vide."})
                    continue

                async def send_status(status: str, label: str) -> None:
                    await _send(ws, {"type": "status", "status": status, "label": label})

                response = await run_agent(
                    session_id=session_id,
                    user_message=user_message,
                    db=db,
                    send_status=send_status,
                )

                await _send(ws, {"type": "message", "role": "assistant", "content": response})

        except WebSocketDisconnect:
            pass
        except Exception as e:
            await _send(ws, {"type": "error", "code": "INTERNAL_ERROR", "message": str(e)})
            await ws.close(code=1011)
