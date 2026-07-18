"""Tests for the ``/api/v1/applications`` endpoints."""

from __future__ import annotations

from httpx import AsyncClient

from tests.helpers import AuthHeaders


async def _create_company(client: AsyncClient, headers: dict[str, str], name: str) -> str:
    response = await client.post("/api/v1/companies", headers=headers, json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_applications_without_auth_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/applications")
    assert response.status_code == 401
    assert response.json()["status"] == 401


async def test_post_application_without_auth_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/applications",
        json={"company_id": "00000000-0000-0000-0000-000000000000", "role_title": "Eng"},
    )
    assert response.status_code == 401


async def test_application_crud(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    headers = auth()
    company_id = await _create_company(client, headers, "Acme")

    create = await client.post(
        "/api/v1/applications",
        headers=headers,
        json={
            "company_id": company_id,
            "role_title": "Senior Engineer",
            "status": "active",
            "salary_min": 100000,
            "salary_max": 150000,
            "salary_currency": "USD",
        },
    )
    assert create.status_code == 201, create.text
    application = create.json()
    application_id = application["id"]
    assert application["role_title"] == "Senior Engineer"
    assert application["status"] == "active"
    assert application["company"]["id"] == company_id
    assert application["company"]["name"] == "Acme"

    listing = await client.get("/api/v1/applications", headers=headers)
    assert listing.status_code == 200
    assert any(a["id"] == application_id for a in listing.json()["items"])

    got = await client.get(f"/api/v1/applications/{application_id}", headers=headers)
    assert got.status_code == 200
    assert got.json()["company"]["id"] == company_id

    patched = await client.patch(
        f"/api/v1/applications/{application_id}",
        headers=headers,
        json={"status": "rejected", "role_title": "Staff Engineer"},
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["status"] == "rejected"
    assert body["role_title"] == "Staff Engineer"

    deleted = await client.delete(f"/api/v1/applications/{application_id}", headers=headers)
    assert deleted.status_code == 204

    assert (
        await client.get(f"/api/v1/applications/{application_id}", headers=headers)
    ).status_code == 404


async def test_application_create_unknown_company_returns_404(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    response = await client.post(
        "/api/v1/applications",
        headers=headers,
        json={
            "company_id": "00000000-0000-0000-0000-000000000000",
            "role_title": "Ghost Role",
        },
    )
    assert response.status_code == 404
    assert response.json()["title"] == "Not Found"


async def test_application_isolation(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    user_a = auth(sub="user_a")
    user_b = auth(sub="user_b")

    company_id = await _create_company(client, user_a, "Owner Co")
    created = await client.post(
        "/api/v1/applications",
        headers=user_a,
        json={"company_id": company_id, "role_title": "Engineer"},
    )
    assert created.status_code == 201
    application_id = created.json()["id"]

    # User B cannot see or mutate user A's application.
    assert (
        await client.get(f"/api/v1/applications/{application_id}", headers=user_b)
    ).status_code == 404
    assert (
        await client.patch(
            f"/api/v1/applications/{application_id}",
            headers=user_b,
            json={"role_title": "Pwned"},
        )
    ).status_code == 404
    assert (
        await client.delete(f"/api/v1/applications/{application_id}", headers=user_b)
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/applications/{application_id}", headers=user_a)
    ).status_code == 200


async def test_application_filters(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    acme = await _create_company(client, headers, "Acme")
    hooli = await _create_company(client, headers, "Hooli")

    await client.post(
        "/api/v1/applications",
        headers=headers,
        json={"company_id": acme, "role_title": "Backend Eng", "status": "active"},
    )
    await client.post(
        "/api/v1/applications",
        headers=headers,
        json={"company_id": hooli, "role_title": "Frontend Eng", "status": "rejected"},
    )

    by_status = await client.get("/api/v1/applications?status=rejected", headers=headers)
    assert by_status.status_code == 200
    statuses = {a["status"] for a in by_status.json()["items"]}
    assert statuses == {"rejected"}

    by_company = await client.get(f"/api/v1/applications?company_id={acme}", headers=headers)
    assert by_company.status_code == 200
    for a in by_company.json()["items"]:
        assert a["company_id"] == acme


async def test_application_unknown_returns_404(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    response = await client.get(
        "/api/v1/applications/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404


async def test_application_bad_body_returns_422(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    response = await client.post(
        "/api/v1/applications", headers=headers, json={"role_title": "Eng"}
    )
    assert response.status_code == 422
    assert response.json()["title"] == "Validation Error"


async def test_create_application_with_company_name_creates_company(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    """Typing a new company name auto-creates the company in the same request."""
    headers = auth()
    create = await client.post(
        "/api/v1/applications",
        headers=headers,
        json={"company_name": "Microsoft", "role_title": "SDE II"},
    )
    assert create.status_code == 201, create.text
    body = create.json()
    assert body["company"]["name"] == "Microsoft"
    company_id = body["company"]["id"]

    # The company now exists in the caller's company list.
    companies = await client.get("/api/v1/companies", headers=headers)
    assert any(
        c["id"] == company_id and c["name"] == "Microsoft" for c in companies.json()["items"]
    )


async def test_create_application_reuses_same_name_company_case_insensitive(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    """A repeated company name reuses the existing row — no duplicate."""
    headers = auth()
    await _create_company(client, headers, "Stripe")

    create = await client.post(
        "/api/v1/applications",
        headers=headers,
        # different casing should still match the existing "Stripe"
        json={"company_name": "stripe", "role_title": "Engineer"},
    )
    assert create.status_code == 201, create.text
    assert create.json()["company"]["name"] == "Stripe"

    # Exactly one company row for "Stripe".
    companies = await client.get("/api/v1/companies?q=tripe", headers=headers)
    assert len([c for c in companies.json()["items"] if c["name"] == "Stripe"]) == 1


async def test_create_application_with_both_company_refs_returns_422(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _create_company(client, headers, "GitHub")
    response = await client.post(
        "/api/v1/applications",
        headers=headers,
        json={"company_id": company_id, "company_name": "GitHub", "role_title": "Eng"},
    )
    assert response.status_code == 422


async def test_company_search_autocomplete_prefix(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    """``/companies/search`` prefix-matches case-insensitively for the combobox."""
    headers = auth()
    await _create_company(client, headers, "Microsoft")
    await _create_company(client, headers, "Microsoft Research")
    await _create_company(client, headers, "Stripe")
    await _create_company(client, headers, "GitHub")

    micr = await client.get("/api/v1/companies/search?q=micr", headers=headers)
    assert micr.status_code == 200
    names = [c["name"] for c in micr.json()]
    assert "Microsoft" in names and "Microsoft Research" in names
    assert "Stripe" not in names and "GitHub" not in names

    # Empty query short-circuits to an empty list.
    empty = await client.get("/api/v1/companies/search?q=%20", headers=headers)
    assert empty.status_code == 200
    assert empty.json() == []


async def test_company_search_is_user_scoped(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    """One user's companies never leak into another user's search results."""
    headers_a = auth()
    await _create_company(client, headers_a, "Acme")

    headers_b = auth(sub="user_other", email="other@test.local")
    results = await client.get("/api/v1/companies/search?q=Acm", headers=headers_b)
    assert results.status_code == 200
    assert results.json() == []
