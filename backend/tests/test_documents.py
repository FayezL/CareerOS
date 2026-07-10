"""Tests for the ``/api/v1/documents`` endpoints."""

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


async def test_document_create_and_upload_then_delete(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    created = await client.post(
        "/api/v1/documents",
        headers=headers,
        json={"type": "resume", "name": "resume.pdf", "mime_type": "application/pdf"},
    )
    assert created.status_code == 201, created.text
    document = created.json()
    document_id = document["id"]
    assert document["name"] == "resume.pdf"
    assert document["upload_method"] == "POST"
    assert document["upload_url"] == f"/api/v1/documents/{document_id}/upload"
    assert document["firebase_path"]

    uploaded = await client.post(
        f"/api/v1/documents/{document_id}/upload",
        headers=headers,
        files={"file": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["size_bytes"] == len(b"%PDF-1.4 fake")

    got = await client.get(f"/api/v1/documents/{document_id}", headers=headers)
    assert got.status_code == 200

    deleted = await client.delete(f"/api/v1/documents/{document_id}", headers=headers)
    assert deleted.status_code == 204
    assert (
        await client.get(f"/api/v1/documents/{document_id}", headers=headers)
    ).status_code == 404


async def test_document_list_and_filters(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _company(client, headers, "Acme")
    application_id = await _application(client, headers, company_id)

    r1 = await client.post(
        "/api/v1/documents",
        headers=headers,
        json={"application_id": application_id, "type": "resume", "name": "a.pdf"},
    )
    await client.post(
        "/api/v1/documents",
        headers=headers,
        json={"type": "cover_letter", "name": "b.pdf"},
    )

    all_docs = await client.get("/api/v1/documents", headers=headers)
    assert all_docs.status_code == 200
    assert len(all_docs.json()["items"]) == 2

    by_app = await client.get(f"/api/v1/documents?application_id={application_id}", headers=headers)
    assert by_app.status_code == 200
    assert all(d["application_id"] == application_id for d in by_app.json()["items"])

    by_type = await client.get("/api/v1/documents?type=cover_letter", headers=headers)
    assert by_type.status_code == 200
    assert all(d["type"] == "cover_letter" for d in by_type.json()["items"])

    by_app_and_type = await client.get(
        f"/api/v1/documents?application_id={application_id}&type=resume", headers=headers
    )
    assert by_app_and_type.status_code == 200
    items = by_app_and_type.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == r1.json()["id"]


async def test_document_unknown_application_404(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    response = await client.post(
        "/api/v1/documents",
        headers=headers,
        json={
            "application_id": "00000000-0000-0000-0000-000000000000",
            "type": "resume",
            "name": "x.pdf",
        },
    )
    assert response.status_code == 404


async def test_document_isolation(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    user_a = auth(sub="user_a")
    user_b = auth(sub="user_b")
    created = await client.post(
        "/api/v1/documents", headers=user_a, json={"type": "resume", "name": "a.pdf"}
    )
    assert created.status_code == 201
    document_id = created.json()["id"]
    assert (await client.get(f"/api/v1/documents/{document_id}", headers=user_b)).status_code == 404
