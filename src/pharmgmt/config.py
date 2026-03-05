"""Application configuration using pydantic-settings."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # Database
    DATABASE_URL: str = "sqlite:///./pharmgmt.db"

    # File storage
    UPLOAD_DIR: str = "./uploads"

    # Logging
    LOG_DIR: str = "./logs"
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = {
        "env_prefix": "PHARM_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
