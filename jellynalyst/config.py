from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Any
import os

class Settings(BaseSettings):
    # Database settings
    DATABASE_HOST: str = "localhost" # default to localhost for local env
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    # API settings
    JELLYSEERR_API_KEY: str
    JELLYSEERR_URL: str
    JELLYFIN_API_KEY: str
    JELLYFIN_URL: str
    TMDB_API_KEY: str

    model_config = {
            "env_file": ".env",
            "case_sensitive": True,
        }

    @property
    def DATABASE_URL(self) -> str:
        """Async database URL for the application"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.DATABASE_HOST}/{self.POSTGRES_DB}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Sync database URL for migrations"""
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.DATABASE_HOST}/{self.POSTGRES_DB}"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # Override DATABASE_HOST if running in Docker
        if os.environ.get("DOCKER_ENV"):
            self.DATABASE_HOST = "db"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
