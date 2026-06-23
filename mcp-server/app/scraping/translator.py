# Traducteur anglais vers français avec Ollama


import hashlib
import json
import logging
import time
from pathlib import Path

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_CACHE_ROOT = Path(__file__).resolve().parents[2] / ".cache" / "translations"

_SYSTEM_PROMPT = (
    "Tu es un traducteur médical spécialisé en rééducation et kinésithérapie. "
    "Traduis fidèlement le texte anglais suivant en français. "
    "Conserve les termes médicaux standards. Ne rajoute aucun commentaire, "
    "aucune explication — uniquement la traduction."
)

# Shared httpx client for all translation requests
_client: httpx.AsyncClient | None = None


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=120.0)
    return _client


def _cache_path(text_hash):
    return _CACHE_ROOT / f"{text_hash}.json"


def _get_cached(text_hash):
    path = _cache_path(text_hash)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload.get("translation")
    except (OSError, json.JSONDecodeError, KeyError):
        return None


def _set_cached(text_hash, translation):
    path = _cache_path(text_hash)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "translated_at": time.time(),
        "translation": translation,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


async def translate_en_to_fr(text, max_chars=4000):
    """Traduit le texte de l'anglais vers le français avec Ollama."""
    if not text or not text.strip():
        return text

    # Truncate very long texts to avoid overwhelming the LLM.
    truncated = text[:max_chars]

    text_hash = hashlib.sha256(truncated.encode("utf-8")).hexdigest()
    cached = _get_cached(text_hash)
    if cached is not None:
        return cached

    ollama_url = f"{settings.OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": settings.OLLAMA_TRANSLATION_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": truncated},
        ],
        "stream": False,
        "think": False,
        "options": {"num_predict": max_chars + 512},
    }

    try:
        client = await _get_client()
        response = await client.post(ollama_url, json=payload)
        response.raise_for_status()
        data = response.json()

        translation = (data.get("message", {}).get("content") or "").strip()
        if not translation:
            logger.warning("Ollama returned empty translation — using original EN text.")
            return truncated

        _set_cached(text_hash, translation)
        return translation

    except Exception as exc:
        logger.warning("Translation failed (%s) — returning original EN text.", exc)
        return truncated
