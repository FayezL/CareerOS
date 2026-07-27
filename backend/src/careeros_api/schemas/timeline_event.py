"""Timeline event request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from careeros_api.models.timeline_event import TimelineEventType, TimelineImportance


class TimelineEventBase(BaseModel):
    """Fields shared across create/read schemas."""

    application_id: uuid.UUID
    event_type: TimelineEventType
    summary: str | None = Field(default=None, max_length=255)
    note: str | None = None
    occurred_at: datetime | None = None
    importance: TimelineImportance = TimelineImportance.NORMAL


class TimelineEventCreate(TimelineEventBase):
    """Payload to create a timeline event.

    ``rejection_reason_category`` is only valid when ``event_type`` is
    ``REJECTED``; the validator below enforces that invariant.
    """

    rejection_reason_category: str | None = None

    @model_validator(mode="after")
    def _validate_rejection_reason(self) -> TimelineEventCreate:
        if (
            self.rejection_reason_category is not None
            and self.event_type != TimelineEventType.REJECTED
        ):
            raise ValueError("rejection_reason_category is only valid when event_type is REJECTED")
        return self


class TimelineEventRead(BaseModel):
    """Public representation of a timeline event."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    event_type: TimelineEventType
    summary: str | None
    note: str | None
    occurred_at: datetime
    importance: TimelineImportance
    follow_up_date: datetime | None
    source: str
    created_at: datetime
    updated_at: datetime
