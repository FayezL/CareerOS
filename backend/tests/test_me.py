"""Tests for the ``/api/v1/me`` profile endpoints."""

from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import AsyncClient

from careeros_api.core.config import settings
from careeros_api.core.security import clerk as clerk_module

KID = "me-test-kid"


def _b64url_int(value: int) -> str:
    byte_length = (value.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(value.to_bytes(byte_length, "big")).rstrip(b"=").decode("ascii")


def _public_jwks(public_key: rsa.RSAPublicKey) -> dict[str, object]:
    numbers = public_key.public_numbers()
    return {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": KID,
        "n": _b64url_int(numbers.n),
        "e": _b64url_int(numbers.e),
    }


def _make_token(private_key: rsa.RSAPrivateKey) -> str:
    now = datetime.now(tz=UTC)
    payload = {
        "sub": "user_me_test",
        "iss": settings.CLERK_ISSUER,
        "iat": now,
        "exp": now + timedelta(hours=1),
        "email": "me@example.com",
        "name": "Me Tester",
    }
    return jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": KID})


async def test_me_without_auth_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me")
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == 401
    assert body["title"] == "Unauthorized"


async def test_me_with_malformed_header_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me", headers={"Authorization": "NotBearer abc"})
    assert response.status_code == 401


@pytest.fixture
def keypair() -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


async def test_me_full_flow(
    client: AsyncClient,
    keypair: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey],
    patch_jwks: object,
    require_db: None,
) -> None:
    private_key, public_key = keypair
    clerk_module._jwks_cache.clear()
    patch_jwks(_public_jwks(public_key))  # type: ignore[operator]
    token = _make_token(private_key)

    # GET /me creates the user on first authenticated request.
    response = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["clerk_user_id"] == "user_me_test"
    assert body["email"] == "me@example.com"
    assert body["full_name"] == "Me Tester"

    # PATCH /me updates mutable fields.
    patched = await client.patch(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Me Updated", "avatar_url": "https://img.example.com/me.png"},
    )
    assert patched.status_code == 200
    patched_body = patched.json()
    assert patched_body["full_name"] == "Me Updated"
    assert patched_body["avatar_url"] == "https://img.example.com/me.png"
