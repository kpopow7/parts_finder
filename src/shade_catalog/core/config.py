from functools import lru_cache

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
