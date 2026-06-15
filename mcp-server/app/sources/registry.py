"""Curated rehabilitation sources — no crawling, only known-good URLs."""

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


# HAS + French public health + hospital PDFs + international patient education.
SOURCE_CATALOG: tuple[SourceEntry, ...] = (
    # --- HAS (France) ---
    SourceEntry(
        key="lombalgie",
        aliases=("dos", "lombalgie", "mal de dos", "back"),
        url="https://www.has-sante.fr/jcms/c_2022459/fr/lombalgie-commune",
        provider="HAS",
        zone="dos",
    ),
    SourceEntry(
        key="genou",
        aliases=("genou", "arthrose genou", "knee"),
        url="https://www.has-sante.fr/jcms/c_2721247/fr/arthrose-du-genou",
        provider="HAS",
        zone="genou",
    ),
    SourceEntry(
        key="epaule",
        aliases=("epaule", "épaule", "coiffe rotateurs", "shoulder"),
        url="https://www.has-sante.fr/jcms/c_2876386/fr/lesions-de-la-coiffe-des-rotateurs",
        provider="HAS",
        zone="epaule",
    ),
    SourceEntry(
        key="apa",
        aliases=("activite physique", "apa", "sport sante"),
        url="https://www.has-sante.fr/jcms/c_2876862/fr/consultation-et-prescription-medicale-d-activite-physique-a-des-fins-de-sante",
        provider="HAS",
    ),
    # --- Santé publique France ---
    SourceEntry(
        key="tms",
        aliases=("tms", "troubles musculo", "membre superieur"),
        url="https://www.santepubliquefrance.fr/maladies-liees-au-travail/troubles-musculo-squelettiques",
        provider="Santé publique France",
        zone="epaule",
    ),
    # --- Hospital PDF livrets (auto-rééducation) ---
    SourceEntry(
        key="neuropathie",
        aliases=("neuropathie", "nerf", "neurologie"),
        url="http://www.neuropathies-peripheriques.org/explorer/documents/LIVRET_auto_reeducation.pdf",
        provider="AP-HP Bicêtre",
        kind="pdf",
        zone="general",
    ),
    SourceEntry(
        key="membre_superieur",
        aliases=("main", "bras", "hemiplegie", "avc", "membre superieur"),
        url="https://www.chu-montpellier.fr/fileadmin/medias/Publications/livret-d-auto-reeducation-du-membre-superieur.pdf",
        provider="CHU Montpellier",
        kind="pdf",
        zone="epaule",
    ),
    # --- MedlinePlus (NIH) — patient exercise sheets ---
    SourceEntry(
        key="rotator_cuff",
        aliases=("coiffe", "rotateur", "rotator cuff"),
        url="https://medlineplus.gov/ency/patientinstructions/000357.htm",
        provider="MedlinePlus (NIH)",
        zone="epaule",
    ),
    SourceEntry(
        key="hip_replacement",
        aliases=("hanche", "prothese hanche", "hip"),
        url="https://medlineplus.gov/ency/patientinstructions/000171.htm",
        provider="MedlinePlus (NIH)",
        zone="hanche",
    ),
    SourceEntry(
        key="back_pain_topic",
        aliases=("lombalgie en", "chronic back"),
        url="https://medlineplus.gov/backpain.html",
        provider="MedlinePlus (NIH)",
        zone="dos",
    ),
    # --- NHS / UK physiotherapy patient resources ---
    SourceEntry(
        key="nhs_back_exercises",
        aliases=("exercices dos", "nhs dos"),
        url="https://www.guysandstthomas.nhs.uk/health-information/low-back-pain/physiotherapy-and-exercises",
        provider="NHS",
        zone="dos",
    ),
    SourceEntry(
        key="nhs_shoulder",
        aliases=("exercices epaule", "nhs epaule"),
        url="https://www.dynamichealth.nhs.uk/help-and-advice/shoulder-pain/",
        provider="NHS",
        zone="epaule",
    ),
    SourceEntry(
        key="nhs_physio",
        aliases=("physiotherapy", "kinesitherapie"),
        url="https://www.nhs.uk/tests-and-treatments/physiotherapy/",
        provider="NHS",
    ),
    # --- CSP (Chartered Society of Physiotherapy) ---
    SourceEntry(
        key="csp_msk",
        aliases=("csp", "douleur articulaire", "msk"),
        url="https://www.csp.org.uk/conditions/managing-pain-home",
        provider="CSP",
    ),
    SourceEntry(
        key="csp_exercises",
        aliases=("csp exercices",),
        url="https://www.csp.org.uk/public-patient/rehabilitation-exercises",
        provider="CSP",
    ),
    # --- VIDAL (reco summaries; single pages only) ---
    SourceEntry(
        key="parkinson",
        aliases=("parkinson",),
        url="https://www.vidal.fr/maladies/recommandations/reeducation-fonctionnelle-parkinson-maladie-de-1740.html",
        provider="VIDAL",
        zone="general",
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
