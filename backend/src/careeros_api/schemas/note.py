"""Note request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoteBase(BaseModel):
    """Fields shared across note create/read schemas."""

    application_id: uuid.UUID | None = None
    contact_id: uuid.UUID | None = None
    content: str = Field(..., min_length=1)


class NoteCreate(NoteBase):
    """Payload to create a note (``content`` required)."""


class NoteUpdate(BaseModel):
    """Partial update for a note; every field is optional."""

    application_id: uuid.UUID | None = None
    contact_id: uuid.UUID | None = None
    content: str | None = Field(default=None, min_length=1)


class NoteRead(BaseModel):
    """Public representation of a note."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID | None
    contact_id: uuid.UUID | None
    content: str
    created_at: datetime
    updated_at: datetime
