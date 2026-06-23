"""Detect broken or non-conformant medical page responses."""

from __future__ import annotations

import re

# Pages that look like errors, homepages, or parked domains — not medical content.
_ERROR_MARKERS = (
    "page non trouvée",
    "erreur 404",
    "not found",
    "introuvable",
    "to acquire this domain",
    "contact sales@physiopedia",
)

# HAS generic portal homepage (old/broken URLs redirect here).
_HAS_HOMEPAGE_MARKERS = (
    "nos priorités",
    "formation diplômante has-ehesp",
    "fortes chaleurs",
    "la has en bref",
)

_REHAB_KEYWORDS = re.compile(
    r"lombalgie|mal de dos|kinésithérapie|kinesitherapie|rééducation|reeducation|"
    r"exercice|physiotherapy|rehabilitation|arthrose|épaule|epaule|genou|"
    r"cervicalgie|entorse|parkinson|avc|douleur|traitement|prescription",
    re.IGNORECASE,
)


def _normalized_text(html: str) -> str:
    return re.sub(r"\s+", " ", html).strip().lower()


def is_error_page(html: str, *, title: str = "") -> bool:
    """True when the response is a 404, parked domain, or similar failure."""
    blob = _normalized_text(f"{title}\n{html}")
    return any(marker in blob for marker in _ERROR_MARKERS)


def is_has_homepage(html: str, url: str) -> bool:
    """True when a HAS URL returned the generic portal instead of a guideline."""
    if "has-sante.fr" not in url.lower():
        return False
    blob = _normalized_text(html)
    if not any(marker in blob for marker in _HAS_HOMEPAGE_MARKERS):
        return False
    # Real guideline pages also mention priorities in nav — require missing rehab topic.
    return not _REHAB_KEYWORDS.search(blob)


def is_content_sufficient(text: str, *, min_chars: int = 250) -> bool:
    """True when extracted body text is long enough to be useful."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    return len(cleaned) >= min_chars


def is_valid_medical_html(html: str, url: str, *, title: str = "") -> bool:
    """Reject responses that are errors, parked pages, or off-topic homepages."""
    if not html or not html.strip():
        return False
    if is_error_page(html, title=title):
        return False
    if is_has_homepage(html, url):
        return False
    return True
