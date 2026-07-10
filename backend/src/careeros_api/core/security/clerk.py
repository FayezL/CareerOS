"""Clerk JWT (RS256) verification against the published JWKS.

The JWKS is cached in-memory per issuer with a TTL and the fetching function is
exposed (``_fetch_jwks``) so that tests can monkeypatch it without performing
any network I/O.
"""

from __future__ import annotations

import json
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm

from careeros_api.core.config import settings
from careeros_api.core.security.errors import AuthError

_JWKS_TTL_SECONDS: float = 3600.0
_JWKSCacheValue = tuple[dict[str, Any], float]

# Issuer -> (jwks payload, monotonic timestamp of last fetch).
_jwks_cache: dict[str, _JWKSCacheValue] = {}


@dataclass(frozen=True)
class CurrentUser:
    """The authenticated principal, derived from a verified Clerk JWT."""

    clerk_user_id: str
    email: str
    full_name: str | None
    avatar_url: str | None


async def _default_fetch_jwks(url: str) -> dict[str, Any]:
    """Fetch the JWKS document from ``url`` using an async HTTP client."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        payload: object = response.json()
    if not isinstance(payload, dict):
        raise TypeError("JWKS endpoint returned a non-object payload")
    return payload


# Indirection point so tests can replace network I/O with a deterministic stub.
_fetch_jwks: Callable[[str], Awaitable[dict[str, Any]]] = _default_fetch_jwks


def _select_key(jwks: dict[str, Any], kid: str) -> Any:
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return RSAAlgorithm.from_jwk(json.dumps(key))
    return None


async def _get_signing_key(kid: str) -> Any:
    """Resolve the RSA public key for ``kid`` using the (cached) JWKS."""
    now = time.monotonic()
    cached = _jwks_cache.get(settings.CLERK_ISSUER)

    if cached is not None and (now - cached[1]) < _JWKS_TTL_SECONDS:
        key = _select_key(cached[0], kid)
        if key is not None:
            return key

    jwks = await _fetch_jwks(settings.CLERK_JWKS_URL)
    _jwks_cache[settings.CLERK_ISSUER] = (jwks, now)

    key = _select_key(jwks, kid)
    if key is None:
        raise AuthError("Unable to find a matching signing key for the token's 'kid'")
    return key


def _require_claim(payload: dict[str, Any], name: str) -> Any:
    if name not in payload:
        raise AuthError(f"Token is missing required claim '{name}'")
    return payload[name]


async def verify_clerk_jwt(token: str) -> CurrentUser:
    """Verify a Clerk-issued JWT and return the authenticated principal.

    Raises:
        AuthError: If the token is malformed, expired, signed by an unknown key,
            issued by the wrong issuer, or missing required claims.
    """
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise AuthError("Token header could not be decoded") from exc

    kid = header.get("kid")
    if not kid:
        raise AuthError("Token header is missing 'kid'")

    try:
        signing_key = await _get_signing_key(kid)
    except AuthError:
        raise
    except Exception as exc:  # noqa: BLE001 - surface any fetch failure as AuthError
        raise AuthError("Failed to retrieve JWKS") from exc

    try:
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=settings.CLERK_ISSUER,
            options={"require": ["exp", "iss", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise AuthError("Token failed verification") from exc

    sub = _require_claim(payload, "sub")
    email = payload.get("email", "")

    return CurrentUser(
        clerk_user_id=sub,
        email=email,
        full_name=payload.get("name") or payload.get("full_name"),
        avatar_url=payload.get("picture") or payload.get("avatar_url"),
    )
