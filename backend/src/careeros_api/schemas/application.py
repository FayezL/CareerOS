"""Application request/response schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from careeros_api.schemas.company import CompanyRead
from careeros_api.schemas.pipeline import PipelineStageRead

ApplicationStatus = Literal["active", "archived", "rejected", "accepted"]


class ApplicationBase(BaseModel):
    """Fields shared across application create/read schemas."""

    role_title: str = Field(..., min_length=1, max_length=255)
    status: ApplicationStatus = "active"
    job_url: str | None = Field(default=None, max_length=2048)
    job_description: str | None = None
    source: str | None = Field(default=None, max_length=255)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    salary_currency: str | None = Field(default=None, min_length=3, max_length=3)
    applied_at: date | None = None


class ApplicationCreate(ApplicationBase):
    """Payload to create an application (``company_id`` + ``role_title`` required)."""

    company_id: uuid.UUID


class ApplicationUpdate(BaseModel):
    """Partial update for an application; every field is optional."""

    company_id: uuid.UUID | None = None
    role_title: str | None = Field(default=None, min_length=1, max_length=255)
    status: ApplicationStatus | None = None
    job_url: str | None = Field(default=None, max_length=2048)
    job_description: str | None = None
    source: str | None = Field(default=None, max_length=255)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    salary_currency: str | None = Field(default=None, min_length=3, max_length=3)
    applied_at: date | None = None


class ApplicationRead(BaseModel):
    """Public representation of an application, with its company embedded."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    role_title: str
    status: ApplicationStatus
    current_stage_id: uuid.UUID | None = None
    job_url: str | None
    job_description: str | None
    source: str | None
    salary_min: int | None
    salary_max: int | None
    salary_currency: str | None
    applied_at: date | None
    company: CompanyRead | None = None
    current_stage: PipelineStageRead | None = None
    created_at: datetime
    updated_at: datetime
