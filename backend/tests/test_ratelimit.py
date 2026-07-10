"""Tests for the in-memory token-bucket rate limiter (isolated app)."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from careeros_api.core.ratelimit import RateLimitMiddleware


async def _ok(_: object) -> JSONResponse:
    return JSONResponse({"ok": True})


def _app(capacity: int) -> Starlette:
    app = Starlette(routes=[Route("/x", _ok)])
    app.add_middleware(RateLimitMiddleware, capacity=capacity, refill_per_minute=capacity)
    return app


async def test_allows_within_capacity() -> None:
    app = _app(capacity=5)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        for _ in range(5):
            response = await client.get("/x")
            assert response.status_code == 200


async def test_over_limit_returns_429() -> None:
    app = _app(capacity=1)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        first = await client.get("/x")
        second = await client.get("/x")
        assert first.status_code == 200
        assert second.status_code == 429
        assert second.headers["content-type"].startswith("application/problem+json")
        assert "Retry-After" in second.headers
        assert second.json()["status"] == 429


async def test_exempt_paths_bypass_limiter() -> None:
    async def root(_: object) -> JSONResponse:
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/", root), Route("/x", _ok)])
    app.add_middleware(RateLimitMiddleware, capacity=1, refill_per_minute=1)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        for _ in range(5):
            response = await client.get("/")
            assert response.status_code == 200
