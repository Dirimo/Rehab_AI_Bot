"""Disk cache for HTTP responses — avoids hammering public medical sites."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

_CACHE_ROOT = Path(__file__).resolve().parents[2] / ".cache" / "http"


def _cache_path(url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return _CACHE_ROOT / f"{digest}.json"


def get_cached(url: str, max_age_seconds: float) -> str | bytes | None:
    """Return cached body if younger than max_age_seconds."""
    path = _cache_path(url)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        age = time.time() - float(payload["fetched_at"])
        if age > max_age_seconds:
            return None
        body = payload["body"]
        if payload.get("binary"):
            return body.encode("latin-1")
        return body
    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        return None


def get_stale(url: str) -> str | bytes | None:
    """Return cache entry regardless of age (fallback when live fetch fails)."""
    path = _cache_path(url)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        body = payload["body"]
        if payload.get("binary"):
            return body.encode("latin-1")
        return body
    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        return None


def set_cached(url: str, body: str | bytes) -> None:
    path = _cache_path(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(body, bytes):
        payload = {
            "url": url,
            "fetched_at": time.time(),
            "binary": True,
            "body": body.decode("latin-1"),
        }
    else:
        payload = {"url": url, "fetched_at": time.time(), "binary": False, "body": body}
    path.write_text(json.dumps(payload), encoding="utf-8")
