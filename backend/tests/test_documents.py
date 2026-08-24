"""Tests for the ``/api/v1/documents`` endpoints."""

from __future__ import annotations

from typing import Any, cast

from httpx import AsyncClient

from tests.helpers import AuthHeaders


async def _company(client: AsyncClient, headers: dict[str, str], name: str) -> str:
    response = await client.post("/api/v1/companies", headers=headers, json={"name": name})
    assert response.status_code == 201, response.text
    return cast(str, response.json()["id"])


async def _application(client: AsyncClient, headers: dict[str, str], company_id: str) -> str:
    response = await client.post(
        "/api/v1/applications",
        headers=headers,
        json={"company_id": company_id, "role_title": "Eng"},
    )
    assert response.status_code == 201, response.text
    return cast(str, response.json()["id"])


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


async def _create_root(
    client: AsyncClient, headers: dict[str, str], doc_type: str = "resume", name: str = "cv.pdf"
) -> str:
    created = await client.post(
        "/api/v1/documents",
        headers=headers,
        json={"type": doc_type, "name": name, "mime_type": "application/pdf"},
    )
    assert created.status_code == 201, created.text
    return cast(str, created.json()["id"])


async def _add_revision(
    client: AsyncClient, headers: dict[str, str], root_id: str, name: str = "cv v2.pdf"
) -> Any:
    return await client.post(
        f"/api/v1/documents/{root_id}/revisions",
        headers=headers,
        json={
            "name": name,
            "mime_type": "application/pdf",
            "version_label": "v2 — Python backend",
        },
    )


async def test_revision_created_on_root(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    root_id = await _create_root(client, headers)

    revision = await _add_revision(client, headers, root_id)
    assert revision.status_code == 201, revision.text
    body = revision.json()
    assert body["parent_document_id"] == root_id
    assert body["version"] == 2
    assert body["is_latest_version"] is True
    assert body["version_label"] == "v2 — Python backend"
    assert body["upload_url"]

    root = (await client.get(f"/api/v1/documents/{root_id}", headers=headers)).json()
    assert root["is_latest_version"] is False


async def test_revision_on_other_users_root_is_404(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    owner, intruder = auth(sub="owner"), auth(sub="intruder")
    root_id = await _create_root(client, owner)

    response = await client.post(
        f"/api/v1/documents/{root_id}/revisions",
        headers=intruder,
        json={
            "name": "steal.pdf",
            "mime_type": "application/pdf",
            "version_label": "stolen",
        },
    )
    assert response.status_code == 404


async def test_revision_on_non_root_is_409(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    root_id = await _create_root(client, headers)
    revision_id = (await _add_revision(client, headers, root_id)).json()["id"]

    response = await client.post(
        f"/api/v1/documents/{revision_id}/revisions",
        headers=headers,
        json={"name": "depth-3.pdf"},
    )
    assert response.status_code == 409


async def test_grouped_list_returns_one_row_per_group(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    root_a = await _create_root(client, headers, name="a.pdf")
    root_b = await _create_root(client, headers, doc_type="cover_letter", name="b.pdf")
    await _add_revision(client, headers, root_a)

    listed = await client.get("/api/v1/documents", headers=headers)
    assert listed.status_code == 200, listed.text
    page = listed.json()
    by_id = {item["id"]: item for item in page["items"]}
    assert len(page["items"]) == 2
    assert by_id.keys() != {root_a, root_b} or by_id[root_a]["is_latest_version"] is False
    reps = {item["parent_document_id"] or item["id"] for item in page["items"]}
    assert reps == {root_a, root_b}
    counts = {
        item["parent_document_id"] or item["id"]: item["revisions_count"] for item in page["items"]
    }
    assert counts[root_a] == 2
    assert counts[root_b] == 1

    flat = (await client.get("/api/v1/documents?include_revisions=true", headers=headers)).json()
    assert len(flat["items"]) == 3
    assert all(item["revisions_count"] is None for item in flat["items"])


async def test_type_filter_with_new_types(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    await _create_root(client, headers, doc_type="visa", name="passport-scan.pdf")
    await _create_root(client, headers, name="cv.pdf")

    listed = await client.get("/api/v1/documents?type=visa", headers=headers)
    assert listed.status_code == 200, listed.text
    assert [item["name"] for item in listed.json()["items"]] == ["passport-scan.pdf"]


async def test_invalid_type_is_422(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    response = await client.post(
        "/api/v1/documents",
        headers=auth(),
        json={"type": "tattoo", "name": "x.pdf"},
    )
    assert response.status_code == 422


async def test_delete_latest_revision_promotes_previous(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    root_id = await _create_root(client, headers)
    revision_id = (await _add_revision(client, headers, root_id)).json()["id"]

    deleted = await client.delete(f"/api/v1/documents/{revision_id}", headers=headers)
    assert deleted.status_code == 204

    root = (await client.get(f"/api/v1/documents/{root_id}", headers=headers)).json()
    assert root["is_latest_version"] is True


async def test_delete_root_cascades(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    root_id = await _create_root(client, headers)
    revision_id = (await _add_revision(client, headers, root_id)).json()["id"]

    deleted = await client.delete(f"/api/v1/documents/{root_id}", headers=headers)
    assert deleted.status_code == 204
    assert (
        await client.get(f"/api/v1/documents/{revision_id}", headers=headers)
    ).status_code == 404


async def test_revision_history_listing(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    root_id = await _create_root(client, headers)
    await _add_revision(client, headers, root_id)

    history = await client.get(f"/api/v1/documents/{root_id}/revisions", headers=headers)
    assert history.status_code == 200, history.text
    items = history.json()
    assert [item["version"] for item in items] == [1, 2]

    non_root = items[1]["id"]
    bad = await client.get(f"/api/v1/documents/{non_root}/revisions", headers=headers)
    assert bad.status_code == 409


async def test_version_index_rejects_duplicate(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    import pytest
    import sqlalchemy as sa
    from sqlalchemy.exc import IntegrityError

    from careeros_api.models.document import Document

    headers = auth()
    root_id = await _create_root(client, headers)
    owner_id = (await client.get("/api/v1/me", headers=headers)).json()["id"]

    from careeros_api.db.session import engine

    async with engine.begin() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(
                sa.insert(Document).values(
                    user_id=owner_id,
                    application_id=None,
                    type="resume",
                    name="collision.pdf",
                    firebase_path="local/dev/collision.pdf",
                    parent_document_id=root_id,
                    version=1,
                    is_latest_version=False,
                )
            )
