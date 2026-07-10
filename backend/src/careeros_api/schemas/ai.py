"""AI generation request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TailorResumeRequest(BaseModel):
    """Request to tailor a resume to a job description."""

    resume_text: str = Field(..., min_length=1)
    job_description: str = Field(..., min_length=1)


class CoverLetterRequest(BaseModel):
    """Request to draft a cover letter."""

    company: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=255)
    resume_text: str = Field(..., min_length=1)


class InterviewPrepRequest(BaseModel):
    """Request to generate interview-prep questions."""

    role: str = Field(..., min_length=1, max_length=255)
    job_description: str = Field(..., min_length=1)


class GenerationResponse(BaseModel):
    """The generated text returned by an AI endpoint."""

    text: str
