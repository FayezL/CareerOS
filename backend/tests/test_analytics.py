"""Tests for the ``/api/v1/analytics`` endpoints (computed from seeded data)."""

from __future__ import annotations

from datetime import date, timedelta

from httpx import AsyncClient

from tests.helpers import AuthHeaders


async def _setup(client: AsyncClient, headers: dict[str, str]) -> dict[str, str]:
    company_id = (
        await client.post("/api/v1/companies", headers=headers, json={"name": "Acme"})
    ).json()["id"]

    async def app(title: str) -> str:
        return (
            await client.post(
                "/api/v1/applications",
                headers=headers,
                json={"company_id": company_id, "role_title": title},
            )
        ).json()["id"]

    stages = (await client.get("/api/v1/pipeline-stages", headers=headers)).json()
    by_name = {s["name"]: str(s["id"]) for s in stages}

    app1 = await app("Backend")
    app2 = await app("Frontend")
    await app("Mobile")  # stays at Applied

    await client.post(
        f"/api/v1/applications/{app1}/move",
        headers=headers,
        json={"to_stage_id": by_name["Interview"]},
    )
    await client.post(
        f"/api/v1/applications/{app2}/move",
        headers=headers,
        json={"to_stage_id": by_name["Offer"]},
    )
    return {"interview_app": app1, "offer_app": app2}


async def test_summary(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    headers = auth()
    await _setup(client, headers)

    response = await client.get("/api/v1/analytics/summary", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    totals = body["totals"]
    assert totals["applications"] == 3
    assert totals["active"] == 3
    assert totals["interviews"] == 1
    assert totals["offers"] == 1
    assert body["response_rate"] == round((1 + 1) / 3, 3)


async def test_funnel(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    headers = auth()
    await _setup(client, headers)

    response = await client.get("/api/v1/analytics/funnel", headers=headers)
    assert response.status_code == 200, response.text
    stages = {s["name"]: s for s in response.json()["stages"]}
    # v2 redesign pipeline (8 stages). The funnel lists all of the caller's
    # stages in position order regardless of whether applications reached them.
    assert [s["name"] for s in response.json()["stages"]] == [
        "Saved",
        "Preparing",
        "Applied",
        "Recruiter Contacted",
        "Interview",
        "Offer",
        "Accepted",
        "Rejected",
    ]
    assert stages["Interview"]["entered"] == 1
    assert stages["Interview"]["distinct_applications"] == 1
    assert stages["Offer"]["entered"] == 1
    assert stages["Offer"]["distinct_applications"] == 1
    assert stages["Applied"]["entered"] == 0
    assert stages["Rejected"]["entered"] == 0


async def test_over_time_day(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    headers = auth()
    await _setup(client, headers)

    today = date.today()
    response = await client.get(
        "/api/v1/analytics/over-time",
        headers=headers,
        params={
            "granularity": "day",
            "from": (today - timedelta(days=7)).isoformat(),
            "to": today.isoformat(),
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["granularity"] == "day"
    assert sum(b["applications"] for b in body["buckets"]) == 3


async def test_over_time_week(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    headers = auth()
    await _setup(client, headers)

    today = date.today()
    response = await client.get(
        "/api/v1/analytics/over-time",
        headers=headers,
        params={
            "granularity": "week",
            "from": (today - timedelta(weeks=2)).isoformat(),
            "to": today.isoformat(),
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["granularity"] == "week"
    assert sum(b["applications"] for b in body["buckets"]) == 3


async def test_analytics_user_scoped(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    user_a = auth(sub="user_a")
    user_b = auth(sub="user_b")
    await _setup(client, user_a)

    response = await client.get("/api/v1/analytics/summary", headers=user_b)
    assert response.status_code == 200
    totals = response.json()["totals"]
    assert totals["applications"] == 0
    assert totals["active"] == 0
    assert response.json()["response_rate"] == 0.0
