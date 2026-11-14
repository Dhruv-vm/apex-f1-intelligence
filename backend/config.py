"""APEX — Application Configuration.

Loads environment variables via pydantic-settings with sensible defaults.
"""

from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable fallback."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Environment
    ENVIRONMENT: str = Field(default="development", description="Execution environment")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging verbosity")

    # Service Bindings
    API_HOST: str = Field(default="127.0.0.1", description="FastAPI bind address")
    API_PORT: int = Field(default=8000, description="FastAPI port")
    FRONTEND_PORT: int = Field(default=3000, description="Next.js frontend port")
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins",
    )

    # Security & Admin Protection
    ADMIN_API_KEY: str = Field(
        default="apex_admin_secret_key_2026",
        description="Secret key required for administrative ingestion endpoints",
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://localhost:5432/apex_f1",
        description="SQLAlchemy relational connection URI",
    )
    DB_ECHO: bool = Field(default=False, description="Echo SQL queries in logs")

    # Data Source Endpoints
    JOLPICA_BASE_URL: str = Field(
        default="https://api.jolpi.ca/ergast/f1",
        description="Ergast/Jolpica REST API base URL",
    )
    OPENF1_BASE_URL: str = Field(
        default="https://api.openf1.org/v1",
        description="OpenF1 Community API base URL",
    )

    # Local Cache Directories
    FASTF1_CACHE_DIR: str = Field(
        default="./data/raw/fastf1_cache",
        description="FastF1 local disk cache directory",
    )
    JOLPICA_CACHE_DIR: str = Field(
        default="./data/raw/jolpica",
        description="Jolpica response disk cache directory",
    )
    OPENF1_CACHE_DIR: str = Field(
        default="./data/raw/openf1",
        description="OpenF1 response disk cache directory",
    )

    # Rate Limiting & Throttling (seconds delay between HTTP calls)
    JOLPICA_RATE_LIMIT_DELAY: float = Field(default=0.25, description="Min seconds between Jolpica requests")
    OPENF1_RATE_LIMIT_DELAY: float = Field(default=0.40, description="Min seconds between OpenF1 requests")
    MAX_RETRIES: int = Field(default=3, description="Max retry attempts on network error")
    TIMEOUT_SECONDS: float = Field(default=15.0, description="HTTP request timeout in seconds")


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton instance of Settings."""
    return Settings()
