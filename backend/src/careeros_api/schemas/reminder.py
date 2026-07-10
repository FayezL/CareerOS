"""Reminder request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReminderCreate(BaseModel):
    """Payload to create a reminder."""

    application_id: uuid.UUID | None = None
    interview_id: uuid.UUID | None = None
    title: str = Field(..., min_length=1, max_length=255)
    due_at: datetime


class ReminderUpdate(BaseModel):
    """Partial update for a reminder; every field is optional."""

    application_id: uuid.UUID | None = None
    interview_id: uuid.UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    due_at: datetime | None = None
    completed_at: datetime | None = None


class SnoozeRequest(BaseModel):
    """Push a reminder's ``due_at`` into the future."""

    due_at: datetime


class ReminderRead(BaseModel):
    """Public representation of a reminder."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID | None
    interview_id: uuid.UUID | None
    title: str
    due_at: datetime
    completed_at: datetime | None
    completed: bool
    created_at: datetime
    updated_at: datetime


class DispatchResult(BaseModel):
    """Summary of a dispatch-due sweep."""

    dispatched: int
