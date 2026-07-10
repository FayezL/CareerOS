"""Polish-layer tests: root health, RFC 7807 for 404/405."""

from __future__ import annotations

from httpx import AsyncClient


async def test_root_health_summary(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "careeros-api"


async def test_unknown_path_returns_rfc7807_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == 404
    assert body["title"] == "Not Found"


async def test_method_not_allowed_returns_rfc7807_405(client: AsyncClient) -> None:
    response = await client.put("/api/v1/health")
    assert response.status_code == 405
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == 405
    assert body["title"] == "Method Not Allowed"


async def test_request_id_header_is_echoed(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health", headers={"X-Request-Id": "abc-123"})
    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == "abc-123"
