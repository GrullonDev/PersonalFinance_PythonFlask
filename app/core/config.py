from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime configuration sourced from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    API_PREFIX: str = Field(default="/api")

    DATABASE_URL: str = Field(default="sqlite:///./personal_finance.db")

    FIREBASE_CREDENTIALS_PATH: str | None = Field(default=None)
    FIREBASE_PROJECT_ID: str | None = Field(default=None)
    ALLOW_TEST_TOKENS: bool = Field(
        default=False,
        description="Permite usar tokens ficticios (uid directo) en entornos no productivos.",
    )

    BACKEND_CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    SMTP_HOST: str | None = Field(default=None)
    SMTP_PORT: int | None = Field(default=None)
    SMTP_USERNAME: str | None = Field(default=None)
    SMTP_PASSWORD: str | None = Field(default=None)
    SMTP_USE_TLS: bool = Field(default=True)
    EMAIL_SENDER: str | None = Field(default=None)
    PASSWORD_RESET_URL: str | None = Field(
        default=None,
        description="URL base usada para construir enlaces de restablecimiento (e.g. https://app/reset?token=)",
    )


@lru_cache
def get_settings() -> Settings:
    """Keep settings as a cached singleton."""
    return Settings()


settings = get_settings()
