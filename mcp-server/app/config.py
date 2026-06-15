"""MCP server configuration (Member 3)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    MCP_HOST: str = "0.0.0.0"
    MCP_PORT: int = 8001

    # Polite crawling: base delay + random jitter between remote requests.
    SCRAPING_RATE_LIMIT_SECONDS: float = 2.0
    SCRAPING_RATE_LIMIT_JITTER_SECONDS: float = 1.5

    # Disk cache TTL — repeat queries rarely hit the network.
    HTTP_CACHE_TTL_SECONDS: float = 7 * 24 * 3600

    # Domains we may fetch (curated public medical / gov sources only).
    ALLOWED_DOMAINS: list[str] = [
        "www.ameli.fr",
        "ameli.fr",
        "www.has-sante.fr",
        "has-sante.fr",
        "www.vidal.fr",
        "vidal.fr",
        "www.santepubliquefrance.fr",
        "santepubliquefrance.fr",
        "medlineplus.gov",
        "www.medlineplus.gov",
        "www.nhs.uk",
        "nhs.uk",
        "www.guysandstthomas.nhs.uk",
        "www.dynamichealth.nhs.uk",
        "www.csp.org.uk",
        "csp.org.uk",
        "www.chu-montpellier.fr",
        "chu-montpellier.fr",
        "www.neuropathies-peripheriques.org",
        "neuropathies-peripheriques.org",
        "www.bradfordhospitals.nhs.uk",
        "www.torbayandsouthdevon.nhs.uk",
    ]


settings = Settings()
