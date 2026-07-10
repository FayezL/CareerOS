"""Pipeline stage request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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
    """Move an application to a different stage, optionally annotating the move."""

    to_stage_id: uuid.UUID
    note: str | None = None


class StageHistoryRead(BaseModel):
    """A single stage-transition record for an application."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    from_stage: PipelineStageRead | None
    to_stage: PipelineStageRead
    changed_at: datetime
    note: str | None
