"""In-memory token-bucket rate limiting.

Each client key (an unverified JWT ``sub`` when a bearer token is present, else
the client IP) gets an independent token bucket refilling at ``RATE_LIMIT_RPM``
tokens per minute up to a capacity of ``RATE_LIMIT_RPM``. Requests beyond the
bucket receive ``429 Too Many Requests`` with a ``Retry-After`` header and an
RFC 7807 problem body.

The limiter is intentionally in-process and is meant for v1 single-instance
deployments; a shared store (Redis) would replace it for horizontal scale.
"""

from __future__ import annotations

import time
from typing import Any, cast

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from careeros_api.core.config import settings
from careeros_api.errors import problem

_EXEMPT_PREFIXES: tuple[str, ...] = (
    "/api/v1/health",
    "/docs",
    "/redoc",
    "/openapi",
)


def _bucket_key(request: Request) -> str:
    """Bucket on the bearer token's ``sub`` when present, else client IP."""
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        token = authorization[len("Bearer ") :]
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            sub = payload.get("sub")
            if isinstance(sub, str) and sub:
                return f"user:{sub}"
        except jwt.PyJWTError:
            pass
    client = request.client.host if request.client else "anonymous"
    return f"ip:{client}"


class _TokenBucket:
    """A simple monotonic-time token bucket."""

    __slots__ = ("capacity", "rate", "tokens", "updated")

    def __init__(self, capacity: float, rate: float, now: float) -> None:
        self.capacity = capacity
        self.rate = rate
        self.tokens = capacity
        self.updated = now

    def consume(self, now: float, cost: float = 1.0) -> tuple[bool, float]:
        """Try to consume ``cost`` tokens; return ``(allowed, retry_after_s)``."""
        elapsed = max(0.0, now - self.updated)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.updated = now
        if self.tokens >= cost:
            self.tokens -= cost
            return True, 0.0
        deficit = cost - self.tokens
        retry_after = deficit / self.rate if self.rate > 0 else 1.0
        return False, retry_after


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-key token-bucket rate limiter."""

    def __init__(self, app: Any, capacity: int, refill_per_minute: int) -> None:
        super().__init__(app)
        self.capacity = float(capacity)
        self.rate = refill_per_minute / 60.0
        self._buckets: dict[str, _TokenBucket] = {}

    def _is_exempt(self, path: str) -> bool:
        return path == "/" or any(path.startswith(prefix) for prefix in _EXEMPT_PREFIXES)

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if self._is_exempt(request.url.path) or self.capacity <= 0:
            return cast("Response", await call_next(request))

        key = _bucket_key(request)
        now = time.monotonic()
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = _TokenBucket(self.capacity, self.rate, now)
            self._buckets[key] = bucket

        allowed, retry_after = bucket.consume(now)
        if not allowed:
            return problem(
                429,
                "Too Many Requests",
                "Rate limit exceeded. Please retry later.",
                headers={"Retry-After": str(int(retry_after) + 1)},
            )
        return cast("Response", await call_next(request))


def rate_limit_capacity() -> int:
    """The configured bucket capacity (requests per minute window)."""
    return int(getattr(settings, "RATE_LIMIT_RPM", 120))
