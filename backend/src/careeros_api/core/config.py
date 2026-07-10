"""Application configuration via pydantic-settings."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _parse_origins(value: Any) -> list[str]:
    """Normalise ``CORS_ORIGINS`` to a list.

    Accepts a comma-separated string (e.g. ``"http://localhost:3000"`` or
    ``"a,b,c"``), a JSON-encoded list, or an already-parsed list/tuple.
    """
    if isinstance(value, str):
        stripped = value.strip()
        return [origin.strip() for origin in stripped.split(",") if origin.strip()]
    if isinstance(value, (list, tuple)):
        return [str(origin) for origin in value]
    return [str(value)]


class Settings(BaseSettings):
    """Strongly-typed, environment-driven application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ENV: Literal["local", "staging", "production"] = "local"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str
    CLERK_ISSUER: str
    CLERK_JWKS_URL: str
    # ``NoDecode`` tells pydantic-settings not to JSON-parse the env value, so the
    # raw comma-separated string reaches the ``before`` validator below.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    # Rate limiting (token bucket per user/IP; v1 is single-instance).
    RATE_LIMIT_RPM: int = 120

    # Object storage. When ``FIREBASE_STORAGE_BUCKET`` is unset, local disk
    # storage under ``UPLOAD_DIR`` is used instead of Firebase.
    FIREBASE_STORAGE_BUCKET: str | None = None
    UPLOAD_DIR: str = "/tmp/careeros-uploads"

    # LLM (AI features). Mock provider when ``LLM_API_KEY`` is unset.
    LLM_API_KEY: str | None = None
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"

    # Billing. Noop provider when ``STRIPE_SECRET_KEY`` is unset.
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None

    # Notifications. Email notifier selected when ``SMTP_HOST`` is set.
    SMTP_HOST: str | None = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: Any) -> list[str]:
        return _parse_origins(value)


# NOTE: the required fields (DATABASE_URL/CLERK_*) are supplied via environment
# variables at runtime by pydantic-settings; mypy (without the pydantic plugin,
# which is intentionally disabled) cannot see that, so the call-arg is expected.
settings = Settings()  # type: ignore[call-arg]
