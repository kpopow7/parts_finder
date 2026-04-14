from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SHADE_CATALOG_",
        env_file=".env",
        extra="ignore",
    )

    env: str = "local"
    debug: bool = False

    # postgresql+asyncpg://user:pass@host:port/db
    database_url: str = "postgresql+asyncpg://shade:shade@127.0.0.1:5432/shade_catalog"
    # postgresql+psycopg://... for Alembic
    sync_database_url: str = "postgresql+psycopg://shade:shade@127.0.0.1:5432/shade_catalog"

    # If set, admin routes require Authorization: Bearer <token>.
    # If unset, admin is open (development only).
    admin_api_token: str | None = None

    # Local filesystem storage for uploads (SVG/PDF). Create this directory on deploy.
    upload_dir: Path = Path("data/uploads")
    max_upload_bytes: int = 25 * 1024 * 1024

    # Comma-separated browser origins for CORS (e.g. http://localhost:5173).
    # Empty = no CORS middleware.
    cors_allow_origins: str = ""

    @field_validator("upload_dir", mode="before")
    @classmethod
    def _coerce_upload_dir(cls, v: str | Path) -> Path:
        return Path(v)


@lru_cache
def get_settings() -> Settings:
    return Settings()
