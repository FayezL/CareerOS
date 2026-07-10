"""Clerk JWT verification tests.

These exercise ``verify_clerk_jwt`` directly using an RSA keypair generated at
runtime, with the JWKS fetch patched out — no network access required.
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from careeros_api.core.config import settings
from careeros_api.core.security import clerk as clerk_module
from careeros_api.core.security.clerk import verify_clerk_jwt
from careeros_api.core.security.errors import AuthError

KID = "test-kid-1234"


def _int_to_base64url(value: int) -> str:
    byte_length = (value.bit_length() + 7) // 8
    raw = value.to_bytes(byte_length, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def generate_keypair() -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def public_jwks(public_key: rsa.RSAPublicKey, kid: str = KID) -> dict[str, object]:
    numbers = public_key.public_numbers()
    return {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": kid,
        "n": _int_to_base64url(numbers.n),
        "e": _int_to_base64url(numbers.e),
    }


def make_token(
    private_key: rsa.RSAPrivateKey,
    *,
    issuer: str | None = None,
    expires_in: timedelta = timedelta(hours=1),
    sub: str = "user_abc",
    extra_claims: dict[str, object] | None = None,
    kid: str = KID,
) -> str:
    now = datetime.now(tz=UTC)
    payload: dict[str, object] = {
        "sub": sub,
        "iss": issuer if issuer is not None else settings.CLERK_ISSUER,
        "iat": now,
        "exp": now + expires_in,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": kid})


async def test_verify_valid_token(
    patch_jwks: object, keypair: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]
) -> None:
    private_key, public_key = keypair
    patch_jwks(public_jwks(public_key))  # type: ignore[operator]
    token = make_token(
        private_key,
        extra_claims={
            "email": "ada@example.com",
            "name": "Ada Lovelace",
            "picture": "https://img.example.com/ada.png",
        },
    )

    current = await verify_clerk_jwt(token)

    assert isinstance(current, clerk_module.CurrentUser)
    assert current.clerk_user_id == "user_abc"
    assert current.email == "ada@example.com"
    assert current.full_name == "Ada Lovelace"
    assert current.avatar_url == "https://img.example.com/ada.png"


async def test_verify_expired_token(
    patch_jwks: object, keypair: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]
) -> None:
    private_key, public_key = keypair
    patch_jwks(public_jwks(public_key))  # type: ignore[operator]
    token = make_token(private_key, expires_in=timedelta(seconds=-10))

    with pytest.raises(AuthError):
        await verify_clerk_jwt(token)


async def test_verify_wrong_issuer(
    patch_jwks: object, keypair: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]
) -> None:
    private_key, public_key = keypair
    patch_jwks(public_jwks(public_key))  # type: ignore[operator]
    token = make_token(private_key, issuer="https://wrong-issuer.example.com")

    with pytest.raises(AuthError):
        await verify_clerk_jwt(token)


async def test_verify_unknown_kid(
    patch_jwks: object, keypair: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]
) -> None:
    private_key, public_key = keypair
    patch_jwks(public_jwks(public_key))  # type: ignore[operator]
    token = make_token(private_key, kid="nonexistent-kid")

    with pytest.raises(AuthError):
        await verify_clerk_jwt(token)


async def test_verify_garbage_token() -> None:
    with pytest.raises(AuthError):
        await verify_clerk_jwt("not-a-real-token")


@pytest.fixture
def keypair() -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    return generate_keypair()
