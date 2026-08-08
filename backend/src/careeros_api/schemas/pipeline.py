"""Pipeline stage request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Rejection categories. Must match the native PG enum `rejection_reason_category`
# (see models/application.py). Validated here so invalid client input returns 422
# instead of leaking to the DB.
RejectionReasonCategory = Literal[
    "visa_sponsorship",
    "lack_of_experience",
    "salary",
    "culture_fit",
    "position_filled",
    "no_feedback",
    "other",
]


class PipelineStageCreate(BaseModel):
    """Payload to create a pipeline stage (``name`` required; appends to the end)."""

    name: str = Field(..., min_length=1, max_length=255)
    color: str | None = Field(default=None, max_length=64)


class PipelineStageUpdate(BaseModel):
    """Partial update for a pipeline stage."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    color: str | None = Field(default=None, max_length=64)


class PipelineStageRead(BaseModel):
    """Public representation of a pipeline stage."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    position: int
    color: str | None
    is_default: bool
    created_at: datetime
    updated_at: datetime


class ReorderStagesRequest(BaseModel):
    """The complete, ordered list of the caller's stage IDs."""

    stage_ids: list[uuid.UUID]


class MoveStageRequest(BaseModel):
    """Move an application to a different stage, optionally annotating the move.

    When the target stage is a rejection stage (name ``"Rejected"``), the
    caller may supply a structured reason that the service writes onto the
    application row for analytics and timeline display.
    """

    to_stage_id: uuid.UUID
    note: str | None = None
    rejection_reason_category: RejectionReasonCategory | None = None
    rejection_reason: str | None = Field(default=None, max_length=255)


class StageHistoryRead(BaseModel):
    """A single stage-transition record for an application."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    from_stage: PipelineStageRead | None
    to_stage: PipelineStageRead
    changed_at: datetime
    note: str | None
