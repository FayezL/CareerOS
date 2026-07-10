"""Endpoints for AI text generation (``/api/v1/ai``).

Feature-flagged: when no ``LLM_API_KEY`` is set, a deterministic mock provider
is used so the endpoints always respond without any network dependency.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from careeros_api.api.deps import CurrentUserDep
from careeros_api.core.llm import LLMClient, get_llm_client
from careeros_api.schemas.ai import (
    CoverLetterRequest,
    GenerationResponse,
    InterviewPrepRequest,
    TailorResumeRequest,
)
from careeros_api.services import ai as ai_service

router = APIRouter(prefix="/ai", tags=["ai"])

LLMClientDep = Annotated[LLMClient, Depends(get_llm_client)]


@router.post("/tailor-resume", response_model=GenerationResponse)
async def tailor_resume(
    request: TailorResumeRequest,
    current_user: CurrentUserDep,
    client: LLMClientDep,
) -> GenerationResponse:
    """Tailor a resume to a job description."""
    del current_user
    text = await ai_service.tailor_resume(request, client)
    return GenerationResponse(text=text)


@router.post("/cover-letter", response_model=GenerationResponse)
async def cover_letter(
    request: CoverLetterRequest,
    current_user: CurrentUserDep,
    client: LLMClientDep,
) -> GenerationResponse:
    """Draft a cover letter for a company and role."""
    del current_user
    text = await ai_service.cover_letter(request, client)
    return GenerationResponse(text=text)


@router.post("/interview-prep", response_model=GenerationResponse)
async def interview_prep(
    request: InterviewPrepRequest,
    current_user: CurrentUserDep,
    client: LLMClientDep,
) -> GenerationResponse:
    """Generate interview-prep questions for a role."""
    del current_user
    text = await ai_service.interview_prep(request, client)
    return GenerationResponse(text=text)
