"""Tests for the ``/api/v1/timeline-events`` endpoints."""

from __future__ import annotations

from httpx import AsyncClient

from tests.helpers import AuthHeaders


async def _create_application(client: AsyncClient, headers: dict[str, str], company_id: str) -> str:
    response = await client.post(
        "/api/v1/applications",
        headers=headers,
        json={
            "company_id": company_id,
            "role_title": "Software Engineer",
            "status": "active",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_company(client: AsyncClient, headers: dict[str, str], name: str) -> str:
    response = await client.post("/api/v1/companies", headers=headers, json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_list_timeline_events(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _create_company(client, headers, "Acme")
    application_id = await _create_application(client, headers, company_id)

    create_1 = await client.post(
        "/api/v1/timeline-events",
        headers=headers,
        json={
            "application_id": application_id,
            "event_type": "PHONE_SCREEN",
            "occurred_at": "2025-01-10T12:00:00Z",
            "summary": "Initial phone screen",
        },
    )
    assert create_1.status_code == 201, create_1.text
    event_1_id = create_1.json()["id"]

    create_2 = await client.post(
        "/api/v1/timeline-events",
        headers=headers,
        json={
            "application_id": application_id,
            "event_type": "ONSITE",
            "occurred_at": "2025-01-15T12:00:00Z",
            "summary": "Onsite interviews",
        },
    )
    assert create_2.status_code == 201, create_2.text
    event_2_id = create_2.json()["id"]

    listing = await client.get(
        "/api/v1/timeline-events",
        headers=headers,
        params={"application_id": application_id},
    )
    assert listing.status_code == 200
    events = listing.json()
    assert len(events) == 2
    assert events[0]["id"] == event_1_id
    assert events[1]["id"] == event_2_id


async def test_create_timeline_event(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _create_company(client, headers, "Acme")
    application_id = await _create_application(client, headers, company_id)

    create = await client.post(
        "/api/v1/timeline-events",
        headers=headers,
        json={
            "application_id": application_id,
            "event_type": "PHONE_SCREEN",
            "occurred_at": "2025-01-10T12:00:00Z",
            "summary": "Initial phone screen with recruiter",
        },
    )
    assert create.status_code == 201
    body = create.json()
    assert body["application_id"] == application_id
    assert body["event_type"] == "PHONE_SCREEN"
    assert body["summary"] == "Initial phone screen with recruiter"
    assert "id" in body


async def test_create_timeline_event_unknown_application_returns_404(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()

    create = await client.post(
        "/api/v1/timeline-events",
        headers=headers,
        json={
            "application_id": "00000000-0000-0000-0000-000000000000",
            "event_type": "PHONE_SCREEN",
            "occurred_at": "2025-01-10T12:00:00Z",
            "summary": "Initial phone screen",
        },
    )
    assert create.status_code == 404
    assert "not found" in create.json()["detail"].lower()


async def test_delete_timeline_event(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _create_company(client, headers, "Acme")
    application_id = await _create_application(client, headers, company_id)

    create = await client.post(
        "/api/v1/timeline-events",
        headers=headers,
        json={
            "application_id": application_id,
            "event_type": "PHONE_SCREEN",
            "occurred_at": "2025-01-10T12:00:00Z",
            "summary": "Initial phone screen",
        },
    )
    assert create.status_code == 201
    event_id = create.json()["id"]

    delete = await client.delete(f"/api/v1/timeline-events/{event_id}", headers=headers)
    assert delete.status_code == 204

    listing = await client.get(
        "/api/v1/timeline-events",
        headers=headers,
        params={"application_id": application_id},
    )
    assert listing.status_code == 200
    events = listing.json()
    assert len(events) == 0


async def test_delete_timeline_event_unknown_event_returns_404(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()

    delete = await client.delete(
        "/api/v1/timeline-events/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert delete.status_code == 404
    assert "not found" in delete.json()["detail"].lower()


async def test_rejection_reason_sync(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _create_company(client, headers, "Acme")
    application_id = await _create_application(client, headers, company_id)

    create_rejected = await client.post(
        "/api/v1/timeline-events",
        headers=headers,
        json={
            "application_id": application_id,
            "event_type": "REJECTED",
            "occurred_at": "2025-01-20T12:00:00Z",
            "summary": "Rejected after onsite",
            "rejection_reason_category": "culture_fit",
        },
    )
    assert create_rejected.status_code == 201

    app = await client.get(f"/api/v1/applications/{application_id}", headers=headers)
    assert app.status_code == 200
    app_body = app.json()
    assert app_body["rejection_reason"] == "Rejected after onsite"
    assert app_body["rejection_reason_category"] == "culture_fit"

    create_another = await client.post(
        "/api/v1/timeline-events",
        headers=headers,
        json={
            "application_id": application_id,
            "event_type": "OFFER",
            "occurred_at": "2025-01-25T12:00:00Z",
            "summary": "Received offer",
        },
    )
    assert create_another.status_code == 201

    listing = await client.get(
        "/api/v1/timeline-events",
        headers=headers,
        params={"application_id": application_id},
    )
    assert listing.status_code == 200
    events = listing.json()
    assert len(events) == 2
    assert events[0]["event_type"] == "REJECTED"
    assert events[1]["event_type"] == "OFFER"


async def test_timeline_events_for_other_users_not_visible(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers_a = auth(sub="user_a", email="a@example.com", name="User A")
    company_id_a = await _create_company(client, headers_a, "Acme")
    application_id_a = await _create_application(client, headers_a, company_id_a)

    create_a = await client.post(
        "/api/v1/timeline-events",
        headers=headers_a,
        json={
            "application_id": application_id_a,
            "event_type": "PHONE_SCREEN",
            "occurred_at": "2025-01-10T12:00:00Z",
            "summary": "User A's event",
        },
    )
    assert create_a.status_code == 201
    event_id_a = create_a.json()["id"]

    headers_b = auth(sub="user_b", email="b@example.com", name="User B")
    company_id_b = await _create_company(client, headers_b, "Beta")
    application_id_b = await _create_application(client, headers_b, company_id_b)

    create_b = await client.post(
        "/api/v1/timeline-events",
        headers=headers_b,
        json={
            "application_id": application_id_b,
            "event_type": "PHONE_SCREEN",
            "occurred_at": "2025-01-15T12:00:00Z",
            "summary": "User B's event",
        },
    )
    assert create_b.status_code == 201
    event_id_b = create_b.json()["id"]

    listing_a = await client.get(
        "/api/v1/timeline-events",
        headers=headers_a,
        params={"application_id": application_id_a},
    )
    assert listing_a.status_code == 200
    events_a = listing_a.json()
    assert len(events_a) == 1
    assert events_a[0]["id"] == event_id_a
    assert events_a[0]["summary"] == "User A's event"

    listing_b = await client.get(
        "/api/v1/timeline-events",
        headers=headers_b,
        params={"application_id": application_id_b},
    )
    assert listing_b.status_code == 200
    events_b = listing_b.json()
    assert len(events_b) == 1
    assert events_b[0]["id"] == event_id_b
    assert events_b[0]["summary"] == "User B's event"

    delete_b = await client.delete(f"/api/v1/timeline-events/{event_id_a}", headers=headers_b)
    assert delete_b.status_code == 404
