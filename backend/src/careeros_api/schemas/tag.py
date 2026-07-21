"""Tag request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TagCreate(BaseModel):
    """Payload to create a tag explicitly (``name`` required)."""

    name: str = Field(..., min_length=1, max_length=255)
    color: str | None = Field(default=None, max_length=64)


class TagRead(BaseModel):
    """Public representation of a tag."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    color: str | None
    created_at: datetime


class TagRef(BaseModel):
    """Minimal tag reference embedded on application reads."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    color: str | None = None
