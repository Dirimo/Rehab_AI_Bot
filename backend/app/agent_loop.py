"""
Agent Loop — Orchestration du flux IA

C'est le cœur du backend : il prépare le contexte, appelle Ollama, gère les tool_calls,
réinjecte les résultats du MCP et retourne la réponse finale au frontend.

► MEMBRE 4 (LLM / Prompts / Contexte) :
    ★ ACTION REQUISE — Remplace SYSTEM_PROMPT par ton prompt système finalisé.
      Le placeholder actuel est fonctionnel mais minimal.

    Points d'intégration :
    - SYSTEM_PROMPT : constante en haut de ce fichier, remplace-la directement.
    - OLLAMA_MODEL : configuré via .env (OLLAMA_MODEL=qwen3:1.7b ou llama3.2).
    - MAX_HISTORY_MESSAGES : nombre de messages d'historique injectés dans le contexte.
      Ajuste cette valeur selon la fenêtre de contexte du modèle choisi.
      Qwen3 1.7B → environ 8 000 tokens → MAX_HISTORY_MESSAGES = 20 (raisonnable)
      LLaMA 3.2  → environ 128 000 tokens → peut monter à 50+
    - Structure du contexte envoyé à Ollama :
        [
          { "role": "system",    "content": SYSTEM_PROMPT },
          { "role": "user",      "content": "message 1" },
          { "role": "assistant", "content": "réponse 1" },
          ...historique...
          { "role": "user",      "content": "nouveau message" },
          # Si tool_call détecté, le cycle continue :
          { "role": "assistant", "content": "", "tool_calls": [...] },
          { "role": "tool",      "content": "{résultat JSON du MCP}" },
        ]
    - Pour définir quand le modèle appelle un tool vs répond directement,
      ajoute des instructions explicites dans SYSTEM_PROMPT (ex: "Appelle search_exercises
      si l'utilisateur demande des exercices pour une pathologie spécifique.").
    - Pour les garde-fous (refus de questions critiques), ajoute-les dans SYSTEM_PROMPT.

► MEMBRE 3 (MCP Server / Scraping) :
    - L'agent loop appelle call_tool() depuis mcp_client.py.
    - MAX_TOOL_ITERATIONS = 5 : le LLM peut enchaîner jusqu'à 5 appels de tools
      avant de forcer une réponse finale.
    - Si ton serveur MCP n'est pas lancé, les tools retournent une erreur JSON
      { "error": "..." } et le LLM reçoit ce message d'erreur comme résultat du tool.

► MEMBRE 1 (Frontend / UX) :
    - La fonction run_agent() envoie des statuts intermédiaires via send_status()
      avant chaque appel Ollama et avant chaque appel MCP.
    - Ces statuts arrivent via WebSocket avec le format :
        { "type": "status", "status": "thinking" | "searching", "label": "..." }
    - Affiche ces statuts dans l'UI comme indicateurs visuels (ex: spinner avec le label).
"""

import json
import os
from collections.abc import Callable, Awaitable
from typing import Any

import httpx
from dotenv import load_dotenv
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Message, ToolLog
from app.mcp_client import AVAILABLE_TOOLS, call_tool

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")
OLLAMA_TIMEOUT = 60.0

# ► MEMBRE 4 : ajuste ces deux constantes selon le modèle choisi
MAX_HISTORY_MESSAGES = 20   # Nombre de messages historiques injectés dans le contexte
MAX_TOOL_ITERATIONS = 5     # Nombre maximum de boucles tool_call avant réponse forcée

# ► MEMBRE 4 : remplace ce prompt par le prompt système finalisé
SYSTEM_PROMPT = """Tu es RehabBot, un assistant pédagogique spécialisé en rééducation physique.

Ton rôle est d'aider les utilisateurs à comprendre les exercices de rééducation, les pathologies musculo-squelettiques et les bonnes pratiques de récupération.

IMPORTANT — Avertissement médical :
- Tu n'es PAS un médecin et tu ne poses JAMAIS de diagnostic.
- Tu ne remplaces pas une consultation médicale ou paramédicale.
- Pour toute douleur aiguë, traumatisme ou symptôme inhabituel, tu recommandes systématiquement de consulter un professionnel de santé.
- Tu refuses de répondre à des questions médicales critiques (dosage médicaments, urgences, etc.).

Comportement :
- Réponds en français, avec un ton clair, pédagogique et bienveillant.
- Utilise les tools disponibles pour chercher des exercices ou des sources fiables quand c'est pertinent.
- Structure tes réponses avec des listes quand tu décris des exercices.
- Si tu n'es pas sûr d'une information, dis-le explicitement.
"""

# Type de la fonction de callback pour envoyer les statuts au frontend via WebSocket
StatusSender = Callable[[str, str], Awaitable[None]]


async def _load_history(session_id: str, db: AsyncSession) -> list[dict[str, str]]:
    """Charge les derniers MAX_HISTORY_MESSAGES messages de la session depuis la BDD."""
    result = await db.exec(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.all()
    tail = messages[-MAX_HISTORY_MESSAGES:] if len(messages) > MAX_HISTORY_MESSAGES else messages
    # On n'injecte que user/assistant dans le contexte (pas les messages "tool" bruts)
    return [{"role": m.role, "content": m.content} for m in tail if m.role in ("user", "assistant")]


async def _save_message(session_id: str, role: str, content: str, db: AsyncSession) -> Message:
    msg = Message(session_id=session_id, role=role, content=content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def _save_tool_log(
    session_id: str,
    message_id: int | None,
    tool_name: str,
    tool_input: dict,
    tool_output: dict,
    duration_ms: int,
    db: AsyncSession,
) -> None:
    """Enregistre l'appel d'un tool dans tool_logs pour audit et debug."""
    log = ToolLog(
        session_id=session_id,
        message_id=message_id,
        tool_name=tool_name,
        tool_input=json.dumps(tool_input, ensure_ascii=False),
        tool_output=json.dumps(tool_output, ensure_ascii=False),
        duration_ms=duration_ms,
    )
    db.add(log)
    await db.commit()


async def _call_ollama(messages: list[dict]) -> dict[str, Any]:
    """Envoie le contexte complet à Ollama et retourne la réponse brute."""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "tools": AVAILABLE_TOOLS,  # Définis dans mcp_client.py
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
        response = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
        response.raise_for_status()
        return response.json()


async def run_agent(
    session_id: str,
    user_message: str,
    db: AsyncSession,
    send_status: StatusSender,
) -> str:
    """
    Boucle principale de l'agent :
    1. Charger l'historique depuis la BDD
    2. Sauvegarder le message utilisateur
    3. Appeler Ollama → si tool_call → appeler MCP → réinjecter → reboucler
    4. Sauvegarder la réponse finale de l'assistant
    5. Retourner le texte final (envoyé au frontend via WebSocket)
    """
    await send_status("thinking", "Analyse de votre message…")

    history = await _load_history(session_id, db)
    await _save_message(session_id, "user", user_message, db)

    context: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    context.extend(history)
    context.append({"role": "user", "content": user_message})

    assistant_msg_id: int | None = None

    for _ in range(MAX_TOOL_ITERATIONS):
        try:
            ollama_response = await _call_ollama(context)
        except httpx.TimeoutException:
            return "Désolé, le modèle ne répond pas. Veuillez réessayer."
        except Exception as e:
            return f"Erreur lors de la communication avec le modèle : {str(e)}"

        message = ollama_response.get("message", {})
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            # Pas de tool_call → réponse finale
            final_text = message.get("content", "").strip()
            saved = await _save_message(session_id, "assistant", final_text, db)
            assistant_msg_id = saved.id
            return final_text

        # Traitement de chaque tool_call émis par le modèle
        for tc in tool_calls:
            fn = tc.get("function", {})
            tool_name = fn.get("name", "")
            tool_input = fn.get("arguments", {})
            if isinstance(tool_input, str):
                try:
                    tool_input = json.loads(tool_input)
                except json.JSONDecodeError:
                    tool_input = {}

            await send_status("searching", f"Recherche via {tool_name}…")

            tool_result = await call_tool(tool_name, tool_input)
            duration_ms = tool_result.get("duration_ms", 0)
            output = tool_result.get("result", {})

            await _save_tool_log(
                session_id=session_id,
                message_id=assistant_msg_id,
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=output,
                duration_ms=duration_ms,
                db=db,
            )

            # Réinjection du résultat dans le contexte pour la prochaine itération
            context.append({"role": "assistant", "content": "", "tool_calls": [tc]})
            context.append({
                "role": "tool",
                "content": json.dumps(output, ensure_ascii=False),
            })

        await send_status("thinking", "Formulation de la réponse…")

    # Sécurité : MAX_TOOL_ITERATIONS atteint sans réponse finale
    fallback = "Je n'ai pas pu obtenir une réponse complète. Veuillez reformuler votre question."
    await _save_message(session_id, "assistant", fallback, db)
    return fallback
