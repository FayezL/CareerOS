"""Tests for the ``/api/v1/reminders`` endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from tests.helpers import AuthHeaders

_FUTURE = (datetime.now(tz=UTC) + timedelta(days=2)).isoformat()
_PAST = (datetime.now(tz=UTC) - timedelta(days=1)).isoformat()


async def test_reminder_crud(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    headers = auth()
    created = await client.post(
        "/api/v1/reminders",
        headers=headers,
        json={"title": "Follow up", "due_at": _FUTURE},
    )
    assert created.status_code == 201, created.text
    reminder = created.json()
    reminder_id = reminder["id"]
    assert reminder["completed"] is False
    assert reminder["completed_at"] is None

    got = await client.get(f"/api/v1/reminders/{reminder_id}", headers=headers)
    assert got.status_code == 200

    listing = await client.get("/api/v1/reminders", headers=headers)
    assert listing.status_code == 200
    assert any(r["id"] == reminder_id for r in listing.json()["items"])

    patched = await client.patch(
        f"/api/v1/reminders/{reminder_id}", headers=headers, json={"title": "Follow up v2"}
    )
    assert patched.status_code == 200
    assert patched.json()["title"] == "Follow up v2"

    assert (
        await client.delete(f"/api/v1/reminders/{reminder_id}", headers=headers)
    ).status_code == 204
    assert (
        await client.get(f"/api/v1/reminders/{reminder_id}", headers=headers)
    ).status_code == 404


async def test_complete_and_snooze(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    reminder_id = (
        await client.post(
            "/api/v1/reminders", headers=headers, json={"title": "Task", "due_at": _FUTURE}
        )
    ).json()["id"]

    complete = await client.post(f"/api/v1/reminders/{reminder_id}/complete", headers=headers)
    assert complete.status_code == 200, complete.text
    assert complete.json()["completed"] is True
    assert complete.json()["completed_at"] is not None

    snoozed = await client.post(
        f"/api/v1/reminders/{reminder_id}/snooze",
        headers=headers,
        json={"due_at": _FUTURE},
    )
    assert snoozed.status_code == 200
    assert snoozed.json()["completed"] is True  # completing persists; snooze only moves due_at


async def test_filter_due_before_and_completed(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    r1 = (
        await client.post(
            "/api/v1/reminders", headers=headers, json={"title": "past", "due_at": _PAST}
        )
    ).json()["id"]
    await client.post(
        "/api/v1/reminders", headers=headers, json={"title": "future", "due_at": _FUTURE}
    )

    due_now = await client.get(
        "/api/v1/reminders",
        headers=headers,
        params={"due_before": datetime.now(tz=UTC).isoformat()},
    )
    due_ids = {r["id"] for r in due_now.json()["items"]}
    assert r1 in due_ids

    await client.post(f"/api/v1/reminders/{r1}/complete", headers=headers)
    pending = await client.get("/api/v1/reminders", headers=headers, params={"completed": "false"})
    assert all(r["id"] != r1 for r in pending.json()["items"])

    done = await client.get("/api/v1/reminders", headers=headers, params={"completed": "true"})
    assert any(r["id"] == r1 for r in done.json()["items"])


async def test_dispatch_due_returns_count(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    await client.post("/api/v1/reminders", headers=headers, json={"title": "due", "due_at": _PAST})
    await client.post(
        "/api/v1/reminders", headers=headers, json={"title": "not yet", "due_at": _FUTURE}
    )

    response = await client.post("/api/v1/reminders/dispatch-due", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["dispatched"] == 1


async def test_reminder_isolation(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    user_a = auth(sub="user_a")
    user_b = auth(sub="user_b")
    reminder_id = (
        await client.post(
            "/api/v1/reminders", headers=user_a, json={"title": "secret", "due_at": _FUTURE}
        )
    ).json()["id"]
    assert (await client.get(f"/api/v1/reminders/{reminder_id}", headers=user_b)).status_code == 404
