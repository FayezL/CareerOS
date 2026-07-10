"""Health-check endpoint tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def test_liveness(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["env"] == "local"


async def test_readiness(client: AsyncClient, require_db: None) -> None:
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.parametrize("path", ["/api/v1/health", "/docs"])
async def test_known_routes(client: AsyncClient, path: str) -> None:
    response = await client.get(path)
    assert response.status_code == 200
