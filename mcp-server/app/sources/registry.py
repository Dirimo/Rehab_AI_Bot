"""Curated rehabilitation sources — only known-good URLs from approved providers.

Providers: HAS (P0), VIDAL (P1), Ameli.fr (P1).
Physiopedia, Axomove, and PMC have their own dedicated modules.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceEntry:
    """One trusted document the MCP server may fetch."""

    key: str
    aliases: tuple[str, ...]
    url: str
    provider: str
    kind: str = "html"  # html | pdf
    zone: str | None = None
    lang: str = "fr"  # fr | en


# ── HAS (P0) — Guidelines & Recommandations officielles ──────────────────────
# ── VIDAL (P1) — Fiches synthétiques par pathologie ──────────────────────────
SOURCE_CATALOG: tuple[SourceEntry, ...] = (
    # --- HAS (France) — P0 ---
    SourceEntry(
        key="lombalgie",
        aliases=("dos", "lombalgie", "mal de dos", "back"),
        url="https://www.has-sante.fr/jcms/c_2961499/fr/prise-en-charge-du-patient-presentant-une-lombalgie-commune",
        provider="HAS",
        zone="dos",
    ),
    SourceEntry(
        key="genou",
        aliases=("genou", "arthrose genou", "knee"),
        url="https://www.has-sante.fr/jcms/p_3360250/fr/synthese-prescription-d-activite-physique-arthroses-peripheriques",
        provider="HAS",
        zone="genou",
    ),
    SourceEntry(
        key="epaule",
        aliases=("epaule", "épaule", "coiffe rotateurs", "shoulder"),
        url="https://www.has-sante.fr/jcms/p_3459565/fr/conduite-diagnostique-devant-une-epaule-douloureuse-non-traumatique-de-l-adulte-et-prise-en-charge-des-tendinopathies-de-la-coiffe-des-rotateurs",
        provider="HAS",
        zone="epaule",
    ),
    SourceEntry(
        key="apa",
        aliases=("activite physique", "apa", "sport sante"),
        url="https://www.has-sante.fr/jcms/c_2876862/fr/consultation-et-prescription-medicale-d-activite-physique-a-des-fins-de-sante",
        provider="HAS",
    ),
    SourceEntry(
        key="has_kinesitherapie",
        aliases=("kinesitherapie", "kinésithérapie", "bilan kiné"),
        url="https://www.has-sante.fr/jcms/c_2876862/fr/consultation-et-prescription-medicale-d-activite-physique-a-des-fins-de-sante",
        provider="HAS",
        zone="general",
    ),
    SourceEntry(
        key="has_cervicalgie",
        aliases=("cervicalgie", "cervicales", "cou", "nuque"),
        url="https://www.has-sante.fr/jcms/c_272262/fr/masso-kinesitherapie-dans-les-cervicalgies-communes-et-dans-le-cadre-du-coup-du-lapin-ou-whiplash",
        provider="HAS",
        zone="cou",
    ),
    SourceEntry(
        key="has_avc",
        aliases=("avc", "hemiplegie", "accident vasculaire"),
        url="https://www.has-sante.fr/jcms/p_3100943/fr/post-avc-quatre-messages-cles-pour-une-reeducation-optimale",
        provider="HAS",
        zone="general",
    ),

    # --- VIDAL (P1) — Rééducation summaries ---
    SourceEntry(
        key="parkinson",
        aliases=("parkinson",),
        url="https://www.vidal.fr/maladies/recommandations/reeducation-fonctionnelle-parkinson-maladie-de-1740.html",
        provider="VIDAL",
        zone="general",
    ),
    SourceEntry(
        key="vidal_lombalgie",
        aliases=("vidal lombalgie", "vidal dos"),
        url="https://www.vidal.fr/maladies/appareil-locomoteur/mal-dos-lombalgie/que-faire.html",
        provider="VIDAL",
        zone="dos",
    ),
    SourceEntry(
        key="vidal_arthrose",
        aliases=("vidal arthrose", "arthrose"),
        url="https://www.vidal.fr/maladies/appareil-locomoteur/arthrose-genou-gonarthrose.html",
        provider="VIDAL",
        zone="genou",
    ),
    SourceEntry(
        key="vidal_tendinite",
        aliases=("tendinite", "tendinopathie"),
        url="https://www.vidal.fr/maladies/appareil-locomoteur/tendinite.html",
        provider="VIDAL",
        zone="epaule",
    ),
    SourceEntry(
        key="vidal_entorse",
        aliases=("entorse", "vidal entorse"),
        url="https://www.vidal.fr/maladies/appareil-locomoteur/entorse-foulure.html",
        provider="VIDAL",
        zone="cheville",
    ),
    SourceEntry(
        key="vidal_sciatique",
        aliases=("sciatique", "sciatalgie", "nerf sciatique"),
        url="https://www.vidal.fr/maladies/appareil-locomoteur/sciatique.html",
        provider="VIDAL",
        zone="dos",
    ),
)

_ALIAS_INDEX: dict[str, SourceEntry] = {}
for entry in SOURCE_CATALOG:
    for alias in entry.aliases:
        _ALIAS_INDEX[alias.lower()] = entry
    _ALIAS_INDEX[entry.key.lower()] = entry


def match_sources(query: str, limit: int = 5) -> list[SourceEntry]:
    """Return catalog entries whose alias appears in the query (longest match first)."""
    q = query.strip().lower()
    if not q:
        return []

    hits: list[tuple[int, SourceEntry]] = []
    seen: set[str] = set()
    for alias, entry in _ALIAS_INDEX.items():
        if alias in q and entry.key not in seen:
            hits.append((len(alias), entry))
            seen.add(entry.key)

    hits.sort(key=lambda item: item[0], reverse=True)
    return [entry for _, entry in hits[:limit]]


def get_by_key(key: str) -> SourceEntry | None:
    return _ALIAS_INDEX.get(key.strip().lower())
