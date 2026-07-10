"""Tests for AI prompt builders, the mock LLM client, and AI endpoints."""

from __future__ import annotations

from httpx import AsyncClient

from careeros_api.core.llm import (
    MockLLMClient,
    cover_letter_prompt,
    get_llm_client,
    interview_prep_prompt,
    tailor_resume_prompt,
)
from tests.helpers import AuthHeaders


def test_tailor_resume_prompt_contains_inputs() -> None:
    prompt = tailor_resume_prompt("MY RESUME", "JOB DESC")
    assert "MY RESUME" in prompt
    assert "JOB DESC" in prompt
    assert prompt.strip()


def test_cover_letter_prompt_contains_inputs() -> None:
    prompt = cover_letter_prompt("Stripe", "Senior Engineer", "MY RESUME")
    assert "Stripe" in prompt
    assert "Senior Engineer" in prompt
    assert "MY RESUME" in prompt


def test_interview_prep_prompt_contains_inputs() -> None:
    prompt = interview_prep_prompt("Staff Engineer", "JOB DESC")
    assert "Staff Engineer" in prompt
    assert "JOB DESC" in prompt


async def test_mock_client_is_deterministic_and_nonempty() -> None:
    client = MockLLMClient()
    out1 = await client.complete("hello\nworld")
    out2 = await client.complete("hello\nworld")
    assert out1
    assert out1 == out2


async def test_default_provider_is_mock_without_key() -> None:
    assert isinstance(get_llm_client(), MockLLMClient)


async def test_ai_tailor_resume_endpoint(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    response = await client.post(
        "/api/v1/ai/tailor-resume",
        headers=headers,
        json={"resume_text": "python backend", "job_description": "fastapi engineer"},
    )
    assert response.status_code == 200, response.text
    text = response.json()["text"]
    assert text


async def test_ai_cover_letter_and_prep_endpoints(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    cover = await client.post(
        "/api/v1/ai/cover-letter",
        headers=headers,
        json={"company": "Stripe", "role": "Backend", "resume_text": "python"},
    )
    assert cover.status_code == 200, cover.text
    assert cover.json()["text"]

    prep = await client.post(
        "/api/v1/ai/interview-prep",
        headers=headers,
        json={"role": "Backend", "job_description": "design systems"},
    )
    assert prep.status_code == 200, prep.text
    assert prep.json()["text"]
