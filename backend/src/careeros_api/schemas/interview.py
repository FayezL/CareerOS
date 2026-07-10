"""Interview request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

InterviewType = Literal["phone", "video", "onsite", "take_home", "offer_call"]


class InterviewBase(BaseModel):
    """Fields shared across interview create/read schemas."""

    type: InterviewType
    scheduled_at: datetime | None = None
    duration_min: int | None = Field(default=None, ge=0)
    location: str | None = Field(default=None, max_length=2048)
    video_url: str | None = Field(default=None, max_length=2048)
    round: int | None = Field(default=None, ge=0)
    notes: str | None = None


class InterviewCreate(InterviewBase):
    """Payload to create an interview (``application_id`` + ``type`` required)."""

    application_id: uuid.UUID


class InterviewUpdate(BaseModel):
    """Partial update for an interview; every field is optional."""

    type: InterviewType | None = None
    scheduled_at: datetime | None = None
    duration_min: int | None = Field(default=None, ge=0)
    location: str | None = Field(default=None, max_length=2048)
    video_url: str | None = Field(default=None, max_length=2048)
    round: int | None = Field(default=None, ge=0)
    notes: str | None = None


class InterviewRead(BaseModel):
    """Public representation of an interview."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    type: InterviewType
    scheduled_at: datetime | None
    duration_min: int | None
    location: str | None
    video_url: str | None
    round: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
