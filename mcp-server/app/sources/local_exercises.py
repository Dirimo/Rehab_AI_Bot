"""Bundled exercise library (offline-first, no scraping)."""

from __future__ import annotations

import json
from pathlib import Path

_BUNDLE_PATH = Path(__file__).resolve().parents[2] / "data" / "exercises_bundle.json"
_exercises: list[dict] | None = None


def _load() -> list[dict]:
    global _exercises
    if _exercises is None:
        raw = json.loads(_BUNDLE_PATH.read_text(encoding="utf-8"))
        _exercises = raw.get("exercises", [])
    return _exercises


def search_exercises(query: str, limit: int = 5) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return []

    scored: list[tuple[int, dict]] = []
    for ex in _load():
        aliases = [a.lower() for a in ex.get("aliases", [])]
        zone = (ex.get("zone") or "").lower()
        name = (ex.get("name") or "").lower()
        score = 0
        for alias in aliases:
            if alias in q:
                score = max(score, len(alias) + 10)
        if zone and zone in q:
            score = max(score, 8)
        if any(word in name for word in q.split() if len(word) > 3):
            score = max(score, 5)
        if score > 0:
            scored.append((score, ex))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [ex for _, ex in scored[:limit]]
