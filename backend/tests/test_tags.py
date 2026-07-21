"""Tests for the ``/api/v1/tags`` endpoints and tag auto-resolution."""

from __future__ import annotations

from httpx import AsyncClient

from tests.helpers import AuthHeaders


async def test_tags_without_auth_returns_401(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/tags")).status_code == 401


async def test_list_seeds_defaults_on_first_access(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    response = await client.get("/api/v1/tags", headers=headers)
    assert response.status_code == 200, response.text
    names = {t["name"] for t in response.json()}
    # A representative slice of the curated defaults.
    assert {"Remote", "Visa Sponsorship", "Python", "Senior"}.issubset(names)


async def test_create_tag_and_reject_duplicate(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    created = await client.post(
        "/api/v1/tags", headers=headers, json={"name": "AWS", "color": "#ff9900"}
    )
    assert created.status_code == 201, created.text
    assert created.json()["name"] == "AWS"
    assert created.json()["color"] == "#ff9900"

    # Case-insensitive duplicate is rejected.
    dup = await client.post("/api/v1/tags", headers=headers, json={"name": "aws"})
    assert dup.status_code == 409


async def test_delete_tag(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    headers = auth()
    created = await client.post("/api/v1/tags", headers=headers, json={"name": "Kubernetes"})
    tag_id = created.json()["id"]
    deleted = await client.delete(f"/api/v1/tags/{tag_id}", headers=headers)
    assert deleted.status_code == 204
    remaining = await client.get("/api/v1/tags", headers=headers)
    assert all(t["id"] != tag_id for t in remaining.json())


async def test_tags_isolated_per_user(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers_a = auth()
    await client.post("/api/v1/tags", headers=headers_a, json={"name": "PrivateA"})

    headers_b = auth(sub="user_b", email="b@example.com")
    response = await client.get("/api/v1/tags", headers=headers_b)
    assert response.status_code == 200
    assert all(t["name"] != "PrivateA" for t in response.json())
