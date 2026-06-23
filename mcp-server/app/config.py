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

    # Ollama (used for EN → FR translation of Physiopedia / PMC content).
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    OLLAMA_TRANSLATION_MODEL: str = "qwen3.5:9b-q4_K_M"

    # Firecrawl — scrape fallback + optional domain-restricted web search.
    FIRECRAWL_API_KEY: str = ""
    FIRECRAWL_ENABLED: bool = True

    # Dynamic discovery (Firecrawl /search on ALLOWED_DOMAINS only).
    DYNAMIC_SEARCH_ENABLED: bool = True
    DYNAMIC_SEARCH_MIN_CATALOG_HITS: int = 2

    # Domains we may fetch (curated public medical / gov sources only).
    ALLOWED_DOMAINS: list[str] = [
        # HAS (P0)
        "www.has-sante.fr",
        "has-sante.fr",
        # VIDAL (P1)
        "www.vidal.fr",
        "vidal.fr",
        # Ameli.fr (P1)
        "www.ameli.fr",
        "ameli.fr",
        # Physiopedia (P0) — live wiki is physio-pedia.com (hyphenated)
        "www.physio-pedia.com",
        "physio-pedia.com",
        "www.physiopedia.com",
        "physiopedia.com",
        # Axomove (P2)
        "www.axomove.com",
        "axomove.com",
        # PMC / NCBI E-utilities (P2) — API, but listed for completeness
        "www.ncbi.nlm.nih.gov",
        "ncbi.nlm.nih.gov",
        "eutils.ncbi.nlm.nih.gov",
    ]


settings = Settings()
