"""AI generation business-logic services."""

from __future__ import annotations

from careeros_api.core.llm import (
    LLMClient,
    cover_letter_prompt,
    interview_prep_prompt,
    tailor_resume_prompt,
)
from careeros_api.schemas.ai import (
    CoverLetterRequest,
    InterviewPrepRequest,
    TailorResumeRequest,
)


async def tailor_resume(request: TailorResumeRequest, client: LLMClient) -> str:
    """Tailor a resume to a job description via ``client``."""
    return await client.complete(tailor_resume_prompt(request.resume_text, request.job_description))


async def cover_letter(request: CoverLetterRequest, client: LLMClient) -> str:
    """Draft a cover letter via ``client``."""
    return await client.complete(
        cover_letter_prompt(request.company, request.role, request.resume_text)
    )


async def interview_prep(request: InterviewPrepRequest, client: LLMClient) -> str:
    """Generate interview-prep questions via ``client``."""
    return await client.complete(interview_prep_prompt(request.role, request.job_description))
