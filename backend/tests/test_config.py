"""Configuration parsing tests."""

from __future__ import annotations

import pytest

from careeros_api.core.config import Settings


def test_default_settings_cors_origins() -> None:
    # When CORS_ORIGINS is unset the default list is used.
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/db",
        CLERK_ISSUER="https://example.clerk.accounts.dev",
        CLERK_JWKS_URL="https://example.clerk.accounts.dev/.well-known/jwks.json",
    )
    assert settings.CORS_ORIGINS == ["http://localhost:3000"]
    assert settings.ENV == "local"


def test_cors_origins_split_from_comma_string(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://example.com")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
    monkeypatch.setenv("CLERK_ISSUER", "https://example.clerk.accounts.dev")
    monkeypatch.setenv("CLERK_JWKS_URL", "https://example.clerk.accounts.dev/jwks.json")

    settings = Settings()
    assert settings.CORS_ORIGINS == ["http://localhost:3000", "https://example.com"]


def test_cors_origins_single_value_from_string(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
    monkeypatch.setenv("CLERK_ISSUER", "https://example.clerk.accounts.dev")
    monkeypatch.setenv("CLERK_JWKS_URL", "https://example.clerk.accounts.dev/jwks.json")

    settings = Settings()
    assert settings.CORS_ORIGINS == ["http://localhost:3000"]


def test_env_values_parsed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
    monkeypatch.setenv("CLERK_ISSUER", "https://clerk.example.com")
    monkeypatch.setenv("CLERK_JWKS_URL", "https://clerk.example.com/jwks.json")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")

    settings = Settings()
    assert settings.ENV == "production"
    assert settings.LOG_LEVEL == "debug"
    assert settings.CLERK_ISSUER == "https://clerk.example.com"
