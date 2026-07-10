"""Company request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompanyBase(BaseModel):
    """Fields shared across company create/read schemas."""

    name: str = Field(..., min_length=1, max_length=255)
    website: str | None = Field(default=None, max_length=2048)
    industry: str | None = Field(default=None, max_length=255)
    size: str | None = Field(default=None, max_length=64)
    location: str | None = Field(default=None, max_length=255)
    linkedin_url: str | None = Field(default=None, max_length=2048)
    notes: str | None = None


class CompanyCreate(CompanyBase):
    """Payload to create a company (``name`` required, rest optional)."""


class CompanyUpdate(BaseModel):
    """Partial update for a company; every field is optional."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    website: str | None = Field(default=None, max_length=2048)
    industry: str | None = Field(default=None, max_length=255)
    size: str | None = Field(default=None, max_length=64)
    location: str | None = Field(default=None, max_length=255)
    linkedin_url: str | None = Field(default=None, max_length=2048)
    notes: str | None = None


class CompanyRead(BaseModel):
    """Public representation of a company."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    website: str | None
    industry: str | None
    size: str | None
    location: str | None
    linkedin_url: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
