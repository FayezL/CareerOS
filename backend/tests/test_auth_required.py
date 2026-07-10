"""Parametrized 401 (unauthorized) checks across every protected v1 path."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

# (method, path, json body). Every entry must require authentication.
PROTECTED: list[tuple[str, str, dict[str, object] | None]] = [
    ("GET", "/api/v1/pipeline-stages", None),
    ("POST", "/api/v1/pipeline-stages", {"name": "X"}),
    ("POST", "/api/v1/pipeline-stages/reorder", {"stage_ids": []}),
    ("GET", "/api/v1/contacts", None),
    ("POST", "/api/v1/contacts", {}),
    ("GET", "/api/v1/interviews", None),
    ("POST", "/api/v1/interviews", {"type": "phone"}),
    ("GET", "/api/v1/notes", None),
    ("POST", "/api/v1/notes", {"content": "x"}),
    ("GET", "/api/v1/documents", None),
    ("POST", "/api/v1/documents", {"type": "resume", "name": "r.pdf"}),
    ("GET", "/api/v1/analytics/summary", None),
    ("GET", "/api/v1/analytics/funnel", None),
    ("GET", "/api/v1/analytics/over-time?from=2026-01-01&to=2026-01-02", None),
    ("GET", "/api/v1/reminders", None),
    ("POST", "/api/v1/reminders", {"title": "x", "due_at": "2026-07-09T16:00:00Z"}),
    ("GET", "/api/v1/billing/subscription", None),
    ("POST", "/api/v1/billing/checkout", {"plan": "pro", "success_url": "s", "cancel_url": "c"}),
    ("POST", "/api/v1/ai/tailor-resume", {"resume_text": "a", "job_description": "b"}),
]


@pytest.mark.parametrize(
    ("method", "path", "body"),
    PROTECTED,
    ids=[f"{m}-{p.split('?')[0]}" for m, p, _ in PROTECTED],
)
async def test_protected_path_requires_auth(
    client: AsyncClient, method: str, path: str, body: dict[str, object] | None
) -> None:
    response = await client.request(method, path, json=body)
    assert response.status_code == 401, response.text
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["status"] == 401
