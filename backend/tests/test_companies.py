"""Tests for the ``/api/v1/companies`` endpoints."""

from __future__ import annotations

from httpx import AsyncClient

from tests.helpers import AuthHeaders


async def test_companies_without_auth_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/companies")
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["status"] == 401


async def test_post_without_auth_returns_401(client: AsyncClient) -> None:
    response = await client.post("/api/v1/companies", json={"name": "Acme"})
    assert response.status_code == 401


async def test_company_crud(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    headers = auth()

    create = await client.post(
        "/api/v1/companies",
        headers=headers,
        json={"name": "Acme Corp", "website": "https://acme.example.com", "industry": "Tech"},
    )
    assert create.status_code == 201, create.text
    company = create.json()
    company_id = company["id"]
    assert company["name"] == "Acme Corp"
    assert company["website"] == "https://acme.example.com"
    assert company["industry"] == "Tech"

    listing = await client.get("/api/v1/companies", headers=headers)
    assert listing.status_code == 200
    page = listing.json()
    assert page["next_cursor"] is None
    assert any(c["id"] == company_id for c in page["items"])

    got = await client.get(f"/api/v1/companies/{company_id}", headers=headers)
    assert got.status_code == 200
    assert got.json()["id"] == company_id

    patched = await client.patch(
        f"/api/v1/companies/{company_id}",
        headers=headers,
        json={"name": "Acme Renamed"},
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Acme Renamed"

    deleted = await client.delete(f"/api/v1/companies/{company_id}", headers=headers)
    assert deleted.status_code == 204

    after_delete = await client.get(f"/api/v1/companies/{company_id}", headers=headers)
    assert after_delete.status_code == 404


async def test_company_search(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    headers = auth()
    await client.post("/api/v1/companies", headers=headers, json={"name": "Initech"})
    await client.post("/api/v1/companies", headers=headers, json={"name": "Hooli"})

    result = await client.get("/api/v1/companies?q=ini", headers=headers)
    assert result.status_code == 200
    names = {c["name"] for c in result.json()["items"]}
    assert "Initech" in names
    assert "Hooli" not in names


async def test_company_isolation(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    user_a = auth(sub="user_a")
    user_b = auth(sub="user_b")

    created = await client.post("/api/v1/companies", headers=user_a, json={"name": "Secret Co"})
    assert created.status_code == 201
    company_id = created.json()["id"]

    # A second user cannot see, update, or delete another user's company.
    assert (await client.get(f"/api/v1/companies/{company_id}", headers=user_b)).status_code == 404
    assert (
        await client.patch(
            f"/api/v1/companies/{company_id}", headers=user_b, json={"name": "Pwned"}
        )
    ).status_code == 404
    assert (
        await client.delete(f"/api/v1/companies/{company_id}", headers=user_b)
    ).status_code == 404

    # The owner still sees the untouched record.
    assert (await client.get(f"/api/v1/companies/{company_id}", headers=user_a)).status_code == 200


async def test_company_unknown_returns_404(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    response = await client.get(
        "/api/v1/companies/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404
    assert response.json()["title"] == "Not Found"


async def test_company_bad_body_returns_422(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    response = await client.post("/api/v1/companies", headers=headers, json={})
    assert response.status_code == 422
    assert response.json()["title"] == "Validation Error"
