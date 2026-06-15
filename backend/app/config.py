"""Central configuration for the RehabBot backend.

All values come from environment variables (or a local `.env` file).
We never hard-code secrets or URLs in the code; we read them here once,
validate their types, and import this single `settings` object everywhere.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Where pydantic-settings looks for variables: a local .env file.
    # Unknown extra variables in the file are ignored (other members may
    # add their own variables to the shared .env).
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database -----------------------------------------------------------
    # SQLAlchemy async connection string. Note the "+psycopg" part: it tells
    # SQLAlchemy to use the psycopg v3 driver in async mode.
    # Example: postgresql+psycopg://user:password@localhost:5432/rehabbot
    DATABASE_URL: str

    # --- Sessions -----------------------------------------------------------
    # The spec: sessions expire automatically after 21 days.
    SESSION_EXPIRATION_DAYS: int = 21

    # --- LLM (Ollama) — used later by the agent loop (Member 4) -------------
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3.5:9b-q4_K_M"
    # Qwen3 "thinking" is slow; disable for faster chat (Ollama API: think=false).
    OLLAMA_THINK: bool = False
    OLLAMA_NUM_PREDICT: int = 1024
    OLLAMA_TIMEOUT_SECONDS: float = 180.0

    # --- MCP server (Member 3) — used later by the agent loop ---------------
    MCP_BASE_URL: str = "http://localhost:8001"

    # --- Agent loop (Member 2) ----------------------------------------------
    AGENT_MAX_HISTORY_MESSAGES: int = 20
    AGENT_MAX_TOOL_ROUNDS: int = 2

    # --- CORS: which frontend origins may call this API ---------------------
    # Nuxt's dev server runs on http://localhost:3000 by default.
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]


# A single shared instance, imported as: from app.config import settings
settings = Settings()
