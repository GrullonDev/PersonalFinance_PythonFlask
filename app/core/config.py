from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, model_validator
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
    LOCAL_AUTH_SECRET: str = Field(
        default="dev-local-secret-change-me",
        description="Clave HMAC usada para firmar tokens locales emitidos por el backend.",
    )
    LOCAL_AUTH_TOKEN_EXPIRES_MINUTES: int = Field(
        default=60,
        description="Minutos de validez para los tokens locales generados tras el login.",
        ge=1,
    )

    @model_validator(mode="after")
    def _ensure_local_auth_secret(self) -> "Settings":
        """Garantiza que `LOCAL_AUTH_SECRET` nunca sea una cadena vacía.

        - En desarrollo (no "production"), si viene vacío desde el entorno,
          forzamos el valor por defecto de desarrollo para evitar errores 500 en
          tiempo de ejecución.
        - En producción, exigimos que tenga un valor no vacío y fallamos
          explícitamente en el arranque con un mensaje claro.
        """
        secret = (self.LOCAL_AUTH_SECRET or "").strip()
        if not secret:
            if self.ENVIRONMENT != "production":
                # Restablece el valor seguro por defecto de dev si el entorno lo
                # proporcionó vacío (lo que eclipsa el default del Field).
                self.LOCAL_AUTH_SECRET = "dev-local-secret-change-me"
            else:
                raise ValueError(
                    "LOCAL_AUTH_SECRET debe estar configurado en producción y no puede estar vacío"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Keep settings as a cached singleton."""
    return Settings()


settings = get_settings()
