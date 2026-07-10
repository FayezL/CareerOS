"""Tests for contacts, interviews, and notes (Phase 3 / people)."""

from __future__ import annotations

from httpx import AsyncClient

from tests.helpers import AuthHeaders


async def _company(client: AsyncClient, headers: dict[str, str], name: str) -> str:
    response = await client.post("/api/v1/companies", headers=headers, json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _application(client: AsyncClient, headers: dict[str, str], company_id: str) -> str:
    response = await client.post(
        "/api/v1/applications",
        headers=headers,
        json={"company_id": company_id, "role_title": "Eng"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


# --------------------------------------------------------------------------- contacts
async def test_contact_crud(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    headers = auth()
    company_id = await _company(client, headers, "Acme")
    created = await client.post(
        "/api/v1/contacts",
        headers=headers,
        json={"company_id": company_id, "first_name": "Priya", "role_title": "recruiter"},
    )
    assert created.status_code == 201, created.text
    contact_id = created.json()["id"]
    assert created.json()["company_id"] == company_id

    listing = await client.get("/api/v1/contacts", headers=headers)
    assert listing.status_code == 200
    assert any(c["id"] == contact_id for c in listing.json()["items"])

    got = await client.get(f"/api/v1/contacts/{contact_id}", headers=headers)
    assert got.status_code == 200

    patched = await client.patch(
        f"/api/v1/contacts/{contact_id}", headers=headers, json={"role_title": "hiring_manager"}
    )
    assert patched.status_code == 200
    assert patched.json()["role_title"] == "hiring_manager"

    deleted = await client.delete(f"/api/v1/contacts/{contact_id}", headers=headers)
    assert deleted.status_code == 204
    assert (await client.get(f"/api/v1/contacts/{contact_id}", headers=headers)).status_code == 404


async def test_contact_filter_by_company(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    acme = await _company(client, headers, "Acme")
    hooli = await _company(client, headers, "Hooli")
    await client.post("/api/v1/contacts", headers=headers, json={"company_id": acme})
    await client.post("/api/v1/contacts", headers=headers, json={"company_id": hooli})

    response = await client.get(f"/api/v1/contacts?company_id={acme}", headers=headers)
    assert response.status_code == 200
    assert all(c["company_id"] == acme for c in response.json()["items"])


async def test_contact_isolation(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    user_a = auth(sub="user_a")
    user_b = auth(sub="user_b")
    created = await client.post("/api/v1/contacts", headers=user_a, json={"first_name": "Secret"})
    assert created.status_code == 201
    contact_id = created.json()["id"]
    assert (await client.get(f"/api/v1/contacts/{contact_id}", headers=user_b)).status_code == 404


# --------------------------------------------------------------------------- interviews
async def test_interview_crud(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    headers = auth()
    company_id = await _company(client, headers, "Acme")
    application_id = await _application(client, headers, company_id)

    created = await client.post(
        "/api/v1/interviews",
        headers=headers,
        json={
            "application_id": application_id,
            "type": "video",
            "scheduled_at": "2026-07-10T16:00:00Z",
            "duration_min": 60,
            "video_url": "https://meet.example/abc",
        },
    )
    assert created.status_code == 201, created.text
    interview_id = created.json()["id"]
    assert created.json()["type"] == "video"

    listing = await client.get("/api/v1/interviews", headers=headers)
    assert listing.status_code == 200
    assert any(i["id"] == interview_id for i in listing.json()["items"])

    patched = await client.patch(
        f"/api/v1/interviews/{interview_id}",
        headers=headers,
        json={"duration_min": 90},
    )
    assert patched.status_code == 200
    assert patched.json()["duration_min"] == 90

    assert (
        await client.get(f"/api/v1/interviews/{interview_id}", headers=headers)
    ).status_code == 200
    assert (
        await client.delete(f"/api/v1/interviews/{interview_id}", headers=headers)
    ).status_code == 204
    assert (
        await client.get(f"/api/v1/interviews/{interview_id}", headers=headers)
    ).status_code == 404


async def test_interview_unknown_application_404(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    response = await client.post(
        "/api/v1/interviews",
        headers=headers,
        json={"application_id": "00000000-0000-0000-0000-000000000000", "type": "phone"},
    )
    assert response.status_code == 404


async def test_interview_filter_by_application(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _company(client, headers, "Acme")
    app1 = await _application(client, headers, company_id)
    app2 = await _application(client, headers, company_id)
    await client.post(
        "/api/v1/interviews", headers=headers, json={"application_id": app1, "type": "phone"}
    )
    await client.post(
        "/api/v1/interviews", headers=headers, json={"application_id": app2, "type": "phone"}
    )

    response = await client.get(f"/api/v1/interviews?application_id={app1}", headers=headers)
    assert response.status_code == 200
    assert all(i["application_id"] == app1 for i in response.json()["items"])


async def test_interview_isolation(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    user_a = auth(sub="user_a")
    user_b = auth(sub="user_b")
    company_id = await _company(client, user_a, "Acme")
    application_id = await _application(client, user_a, company_id)
    created = await client.post(
        "/api/v1/interviews",
        headers=user_a,
        json={"application_id": application_id, "type": "phone"},
    )
    assert created.status_code == 201
    interview_id = created.json()["id"]
    assert (
        await client.get(f"/api/v1/interviews/{interview_id}", headers=user_b)
    ).status_code == 404


# --------------------------------------------------------------------------- notes
async def test_note_crud(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    headers = auth()
    created = await client.post("/api/v1/notes", headers=headers, json={"content": "first note"})
    assert created.status_code == 201, created.text
    note_id = created.json()["id"]
    assert created.json()["content"] == "first note"

    listing = await client.get("/api/v1/notes", headers=headers)
    assert listing.status_code == 200
    assert any(n["id"] == note_id for n in listing.json()["items"])

    patched = await client.patch(
        f"/api/v1/notes/{note_id}", headers=headers, json={"content": "updated"}
    )
    assert patched.status_code == 200
    assert patched.json()["content"] == "updated"

    assert (await client.delete(f"/api/v1/notes/{note_id}", headers=headers)).status_code == 204
    assert (await client.get(f"/api/v1/notes/{note_id}", headers=headers)).status_code == 404


async def test_note_filter_by_application(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _company(client, headers, "Acme")
    app1 = await _application(client, headers, company_id)
    await client.post(
        "/api/v1/notes", headers=headers, json={"application_id": app1, "content": "a"}
    )
    await client.post("/api/v1/notes", headers=headers, json={"content": "b"})

    response = await client.get(f"/api/v1/notes?application_id={app1}", headers=headers)
    assert response.status_code == 200
    assert all(n["application_id"] == app1 for n in response.json()["items"])


async def test_note_isolation(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    user_a = auth(sub="user_a")
    user_b = auth(sub="user_b")
    created = await client.post("/api/v1/notes", headers=user_a, json={"content": "secret"})
    assert created.status_code == 201
    note_id = created.json()["id"]
    assert (await client.get(f"/api/v1/notes/{note_id}", headers=user_b)).status_code == 404
