"""LLM client abstraction for AI text-generation features.

* ``MockLLMClient`` — deterministic, templated output (selected when
  ``LLM_API_KEY`` is unset; used in tests and local dev).
* ``OpenAICompatibleClient`` — calls an OpenAI-compatible chat-completions
  endpoint over HTTP (selected when ``LLM_API_KEY`` is set).

Prompt builders are module-level functions so they can be unit-tested without
any network or provider.
"""

from __future__ import annotations

import httpx

from careeros_api.core.config import settings

_DEFAULT_MODEL = "gpt-4o-mini"


class LLMClient:
    """Abstract chat-completion client."""

    async def complete(self, prompt: str) -> str:
        raise NotImplementedError


class MockLLMClient(LLMClient):
    """Deterministic client that echoes a templated summary of the prompt.

    The output is stable for a given prompt so tests can assert on it. It is
    intentionally non-empty and references the inputs so the higher-level
    generation flows are exercised meaningfully without a network call.
    """

    async def complete(self, prompt: str) -> str:
        marker = prompt.splitlines()[0] if prompt.strip() else "request"
        body = prompt.strip()
        return (
            f"[mock-llm] {marker}\n"
            f"Generated the following based on {len(body)} characters of input:\n"
            f"{body[:280]}"
        )


class OpenAICompatibleClient(LLMClient):
    """Client for an OpenAI-compatible ``/chat/completions`` endpoint."""

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def complete(self, prompt: str) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        choices = data.get("choices") or [{}]
        content = choices[0].get("message", {}).get("content", "")
        return str(content).strip()


def get_llm_client() -> LLMClient:
    """Return the configured LLM client (mock when no API key is set)."""
    api_key = getattr(settings, "LLM_API_KEY", None)
    if api_key:
        base_url = getattr(settings, "LLM_BASE_URL", "https://api.openai.com/v1")
        model = getattr(settings, "LLM_MODEL", _DEFAULT_MODEL)
        return OpenAICompatibleClient(base_url, api_key, model)
    return MockLLMClient()


def tailor_resume_prompt(resume_text: str, job_description: str) -> str:
    """Build the prompt for tailoring a resume to a job description."""
    return (
        "Tailor the following resume to the job description. "
        "Reorder, emphasize, and reword relevant experience; keep it truthful.\n"
        f"\nJOB DESCRIPTION:\n{job_description}\n"
        f"\nRESUME:\n{resume_text}\n"
    ).strip()


def cover_letter_prompt(company: str, role: str, resume_text: str) -> str:
    """Build the prompt for drafting a cover letter."""
    return (
        f"Write a concise, professional cover letter for the {role} role at {company}, "
        "grounded in the candidate's resume. Do not invent employers or dates.\n"
        f"\nRESUME:\n{resume_text}\n"
    ).strip()


def interview_prep_prompt(role: str, job_description: str) -> str:
    """Build the prompt for generating interview-prep questions."""
    return (
        f"Generate a focused list of interview preparation questions for the {role} role, "
        "tailored to the job description. Include a mix of behavioural and technical items.\n"
        f"\nJOB DESCRIPTION:\n{job_description}\n"
    ).strip()
