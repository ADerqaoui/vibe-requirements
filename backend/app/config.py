"""Application configuration loaded from environment / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. Secrets come from .env and never touch the database."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "sqlite:///./reqdash.db"
    auto_migrate_on_startup: bool = True

    # Ollama (local LLM host)
    ollama_host: str = "http://localhost:11434"
    ollama_timeout_seconds: float = 120.0
    cloud_timeout_seconds: float = 60.0
    llm_retry_count: int = 2

    # Cloud provider keys (blank = provider disabled). Read from .env only.
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    deepseek_api_key: str = ""

    # App
    app_port: int = 8000
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
