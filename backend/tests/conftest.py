"""Shared pytest fixtures and test-environment setup.

The required application settings must exist before any ``careeros_api`` module is
imported (they are constructed at import time). We install deterministic defaults
here so that the suite can run without a real database or Clerk tenant; tests
that genuinely require a database skip themselves when it is unreachable.
"""

from __future__ import annotations

import os

# --- Provide deterministic settings *before* importing the application. -------
_DEFAULTS: dict[str, str] = {
    "ENV": "local",
    "LOG_LEVEL": "WARNING",
    "DATABASE_URL": "postgresql+asyncpg://careeros:careeros@localhost:5432/careeros",
    "CLERK_ISSUER": "https://example.clerk.accounts.dev",
    "CLERK_JWKS_URL": "https://example.clerk.accounts.dev/.well-known/jwks.json",
    "CORS_ORIGINS": "http://localhost:3000",
    # High limit so the suite never trips the in-process rate limiter; the
    # limiter itself is exercised in isolation in test_ratelimit.
    "RATE_LIMIT_RPM": "100000",
}
for _key, _value in _DEFAULTS.items():
    os.environ.setdefault(_key, _value)

from collections.abc import AsyncIterator, Callable
from typing import Any

import pytest
import pytest_asyncio
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from careeros_api.core.security import clerk as clerk_module
from careeros_api.main import app
from tests.helpers import generate_keypair, make_token, public_jwks


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """An ``httpx.AsyncClient`` wired to the FastAPI app via ASGI transport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


async def _db_is_available() -> bool:
    from careeros_api.db.session import engine

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 - any failure means "no database"
        return False


@pytest_asyncio.fixture
async def require_db() -> None:
    """Skip the requesting test if the database is not reachable."""
    if not await _db_is_available():
        pytest.skip("DATABASE_URL is not reachable")


def make_jwks(public_jwk: dict[str, Any]) -> Any:
    """Return an async JWKS-fetch callable returning ``public_jwk`` as the sole key."""

    async def _fetch(_url: str) -> dict[str, Any]:
        return {"keys": [public_jwk]}

    return _fetch


@pytest.fixture
def patch_jwks(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Patch the Clerk JWKS fetcher and clear the JWKS cache for the duration."""

    def _apply(public_jwk: dict[str, Any]) -> None:
        clerk_module._jwks_cache.clear()
        monkeypatch.setattr(clerk_module, "_fetch_jwks", make_jwks(public_jwk))

    return _apply


@pytest.fixture
def keypair() -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """Generate a deterministic RSA keypair for the test session."""
    return generate_keypair()


@pytest.fixture
def auth(
    patch_jwks: Any, keypair: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]
) -> Callable[..., dict[str, str]]:
    """Patch the JWKS once and return a helper that issues auth headers for a sub."""
    private_key, public_key = keypair
    clerk_module._jwks_cache.clear()
    patch_jwks(public_jwks(public_key))

    def _headers(
        *,
        sub: str = "user_a",
        email: str = "a@example.com",
        name: str = "User A",
    ) -> dict[str, str]:
        token = make_token(private_key, sub=sub, extra_claims={"email": email, "name": name})
        return {"Authorization": f"Bearer {token}"}

    return _headers
