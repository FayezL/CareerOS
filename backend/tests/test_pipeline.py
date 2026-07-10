"""Tests for the ``/api/v1/pipeline-stages`` endpoints and stage moves."""

from __future__ import annotations

from httpx import AsyncClient

from tests.helpers import AuthHeaders


async def _stages(client: AsyncClient, headers: dict[str, str]) -> list[dict[str, object]]:
    response = await client.get("/api/v1/pipeline-stages", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


async def _create_company(client: AsyncClient, headers: dict[str, str], name: str) -> str:
    response = await client.post("/api/v1/companies", headers=headers, json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_application(client: AsyncClient, headers: dict[str, str], company_id: str) -> str:
    response = await client.post(
        "/api/v1/applications",
        headers=headers,
        json={"company_id": company_id, "role_title": "Eng"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_default_stages_seeded(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    stages = await _stages(client, headers)
    names = [s["name"] for s in stages]
    assert names == ["Applied", "Screening", "Interview", "Offer", "Accepted", "Rejected"]
    assert all(s["is_default"] for s in stages)
    assert [s["position"] for s in stages] == [0, 1, 2, 3, 4, 5]


async def test_stage_crud(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    headers = auth()
    created = await client.post(
        "/api/v1/pipeline-stages", headers=headers, json={"name": "Team Match", "color": "#fbbf24"}
    )
    assert created.status_code == 201, created.text
    stage = created.json()
    assert stage["name"] == "Team Match"
    assert stage["position"] == 6
    assert stage["color"] == "#fbbf24"

    patched = await client.patch(
        f"/api/v1/pipeline-stages/{stage['id']}", headers=headers, json={"name": "Team Fit"}
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Team Fit"

    deleted = await client.delete(f"/api/v1/pipeline-stages/{stage['id']}", headers=headers)
    assert deleted.status_code == 204

    assert (await client.get("/api/v1/pipeline-stages", headers=headers)).json()


async def test_reorder_stages(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    headers = auth()
    stages = await _stages(client, headers)
    ids = [str(s["id"]) for s in stages]
    reversed_ids = list(reversed(ids))

    response = await client.post(
        "/api/v1/pipeline-stages/reorder", headers=headers, json={"stage_ids": reversed_ids}
    )
    assert response.status_code == 200, response.text
    reordered = response.json()
    assert [s["id"] for s in reordered] == reversed_ids
    assert [s["position"] for s in reordered] == [0, 1, 2, 3, 4, 5]


async def test_reorder_rejects_partial_set(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    stages = await _stages(client, headers)
    partial = [str(stages[0]["id"]), str(stages[1]["id"])]
    response = await client.post(
        "/api/v1/pipeline-stages/reorder", headers=headers, json={"stage_ids": partial}
    )
    assert response.status_code == 409


async def test_move_sets_stage_and_appends_history(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _create_company(client, headers, "Movers Co")
    application_id = await _create_application(client, headers, company_id)
    stages = await _stages(client, headers)
    applied_id = str(stages[0]["id"])
    screening_id = str(stages[1]["id"])

    move = await client.post(
        f"/api/v1/applications/{application_id}/move",
        headers=headers,
        json={"to_stage_id": screening_id, "note": "recruiter call"},
    )
    assert move.status_code == 200, move.text
    moved = move.json()
    assert moved["current_stage_id"] == screening_id
    assert moved["current_stage"]["id"] == screening_id

    history = await client.get(f"/api/v1/applications/{application_id}/history", headers=headers)
    assert history.status_code == 200, history.text
    rows = history.json()
    assert len(rows) == 1
    assert rows[0]["to_stage"]["id"] == screening_id
    assert rows[0]["note"] == "recruiter call"
    assert rows[0]["from_stage"] is None

    # Move back to Applied adds a second history row.
    await client.post(
        f"/api/v1/applications/{application_id}/move",
        headers=headers,
        json={"to_stage_id": applied_id},
    )
    rows = (
        await client.get(f"/api/v1/applications/{application_id}/history", headers=headers)
    ).json()
    assert len(rows) == 2


async def test_delete_stage_in_use_returns_409(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _create_company(client, headers, "Stage Co")
    application_id = await _create_application(client, headers, company_id)
    stages = await _stages(client, headers)
    interview_id = str(stages[2]["id"])

    await client.post(
        f"/api/v1/applications/{application_id}/move",
        headers=headers,
        json={"to_stage_id": interview_id},
    )
    response = await client.delete(f"/api/v1/pipeline-stages/{interview_id}", headers=headers)
    assert response.status_code == 409


async def test_pipeline_isolation(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    user_a = auth(sub="user_a")
    user_b = auth(sub="user_b")

    stages_a = await _stages(client, user_a)
    # User B has an independent set of default stages.
    stages_b = await _stages(client, user_b)
    assert {s["id"] for s in stages_a}.isdisjoint({s["id"] for s in stages_b})

    a_stage = str(stages_a[0]["id"])
    # User B cannot see/delete user A's stage.
    assert (
        await client.delete(f"/api/v1/pipeline-stages/{a_stage}", headers=user_b)
    ).status_code == 404
