"""Shared test utilities for issuing RS256 JWTs against a patched JWKS.

Reused across the company/application endpoint tests; mirrors the pattern in
``tests/test_me.py`` and ``tests/test_clerk_verification.py`` but supports an
arbitrary ``sub`` so that per-user isolation can be exercised.
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from careeros_api.core.config import settings

KID = "crud-test-kid"


class AuthHeaders(Protocol):
    """Callable protocol describing the ``auth`` fixture's return value."""

    def __call__(
        self,
        *,
        sub: str = ...,
        email: str = ...,
        name: str = ...,
    ) -> dict[str, str]: ...


def generate_keypair() -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """Generate a fresh RSA keypair for signing test tokens."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def _b64url_int(value: int) -> str:
    byte_length = (value.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(value.to_bytes(byte_length, "big")).rstrip(b"=").decode("ascii")


def public_jwks(public_key: rsa.RSAPublicKey, kid: str = KID) -> dict[str, object]:
    """Build a single-key JWKS document for ``public_key``."""
    numbers = public_key.public_numbers()
    return {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": kid,
        "n": _b64url_int(numbers.n),
        "e": _b64url_int(numbers.e),
    }


def make_token(
    private_key: rsa.RSAPrivateKey,
    *,
    sub: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Sign a short-lived JWT with the given ``sub`` and optional claims."""
    now = datetime.now(tz=UTC)
    payload: dict[str, Any] = {
        "sub": sub,
        "iss": settings.CLERK_ISSUER,
        "iat": now,
        "exp": now + timedelta(hours=1),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": KID})
