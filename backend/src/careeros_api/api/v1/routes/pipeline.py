"""Endpoints for the authenticated user's pipeline stages (``/api/v1/pipeline-stages``)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Response, status

from careeros_api.api.deps import CurrentUserDep, SessionDep
from careeros_api.schemas.pipeline import (
    PipelineStageCreate,
    PipelineStageRead,
    PipelineStageUpdate,
    ReorderStagesRequest,
)
from careeros_api.services import pipeline as pipeline_service

router = APIRouter(prefix="/pipeline-stages", tags=["pipeline"])


@router.get("", response_model=list[PipelineStageRead])
async def list_stages(
    session: SessionDep,
    current_user: CurrentUserDep,
) -> list[PipelineStageRead]:
    """Return all of the caller's pipeline stages, ordered by position."""
    return await pipeline_service.list_stages(session, current_user)


@router.post("", response_model=PipelineStageRead, status_code=status.HTTP_201_CREATED)
async def create_stage(
    session: SessionDep,
    current_user: CurrentUserDep,
    data: PipelineStageCreate,
) -> PipelineStageRead:
    """Create a new pipeline stage appended to the caller's board."""
    return await pipeline_service.create_stage(session, current_user, data)


@router.post("/reorder", response_model=list[PipelineStageRead])
async def reorder_stages(
    session: SessionDep,
    current_user: CurrentUserDep,
    data: ReorderStagesRequest,
) -> list[PipelineStageRead]:
    """Atomically reorder all of the caller's pipeline stages."""
    return await pipeline_service.reorder_stages(session, current_user, data)


@router.patch("/{stage_id}", response_model=PipelineStageRead)
async def update_stage(
    session: SessionDep,
    current_user: CurrentUserDep,
    stage_id: uuid.UUID,
    data: PipelineStageUpdate,
) -> PipelineStageRead:
    """Partially update a pipeline stage owned by the caller."""
    return await pipeline_service.update_stage(session, current_user, stage_id, data)


@router.delete("/{stage_id}")
async def delete_stage(
    session: SessionDep,
    current_user: CurrentUserDep,
    stage_id: uuid.UUID,
) -> Response:
    """Delete a pipeline stage owned by the caller (409 if still in use)."""
    await pipeline_service.delete_stage(session, current_user, stage_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
