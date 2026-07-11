"""Pipeline stage business-logic services."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.errors import ConflictError, NotFoundError
from careeros_api.models.pipeline_stage import PipelineStage
from careeros_api.models.user import User
from careeros_api.repositories.pipeline import PipelineStageRepository
from careeros_api.schemas.pipeline import (
    PipelineStageCreate,
    PipelineStageRead,
    PipelineStageUpdate,
    ReorderStagesRequest,
)

_DEFAULT_STAGES: list[tuple[str, int]] = [
    ("Applied", 0),
    ("Screening", 1),
    ("Interview", 2),
    ("Offer", 3),
    ("Accepted", 4),
    ("Rejected", 5),
]


async def ensure_default_stages(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Create the seeded default stages for ``user_id`` if none exist yet."""
    repo = PipelineStageRepository(session)
    if await repo.count(user_id) > 0:
        return
    for name, position in _DEFAULT_STAGES:
        session.add(PipelineStage(user_id=user_id, name=name, position=position, is_default=True))
    await session.flush()


async def list_stages(session: AsyncSession, user: User) -> list[PipelineStageRead]:
    """Return the caller's stages, seeding defaults on first access."""
    await ensure_default_stages(session, user.id)
    repo = PipelineStageRepository(session)
    stages = await repo.list_ordered(user.id)
    return [PipelineStageRead.model_validate(s) for s in stages]


async def create_stage(
    session: AsyncSession, user: User, data: PipelineStageCreate
) -> PipelineStageRead:
    """Create a new stage appended to the caller's pipeline."""
    await ensure_default_stages(session, user.id)
    repo = PipelineStageRepository(session)
    stage = await repo.create(user.id, data)
    return PipelineStageRead.model_validate(stage)


async def update_stage(
    session: AsyncSession,
    user: User,
    stage_id: uuid.UUID,
    data: PipelineStageUpdate,
) -> PipelineStageRead:
    """Partially update a stage owned by the caller."""
    repo = PipelineStageRepository(session)
    stage = await repo.get(user.id, stage_id)
    if stage is None:
        raise NotFoundError(f"Pipeline stage {stage_id} not found")
    updated = await repo.update(stage, data)
    return PipelineStageRead.model_validate(updated)


async def delete_stage(session: AsyncSession, user: User, stage_id: uuid.UUID) -> None:
    """Delete a stage owned by the caller.

    Raises ``ConflictError`` if any application still references the stage.
    """
    repo = PipelineStageRepository(session)
    stage = await repo.get(user.id, stage_id)
    if stage is None:
        raise NotFoundError(f"Pipeline stage {stage_id} not found")
    if await repo.count_applications(stage_id) > 0:
        raise ConflictError("Pipeline stage is in use by one or more applications")
    await repo.delete(stage)


async def reorder_stages(
    session: AsyncSession, user: User, data: ReorderStagesRequest
) -> list[PipelineStageRead]:
    """Renumber the caller's stages to match the provided ordering.

    The provided IDs must contain exactly the caller's stages (no more, no less)
    or a ``ConflictError`` is raised.
    """
    repo = PipelineStageRepository(session)
    existing = await repo.list_ordered(user.id)
    existing_ids = {s.id for s in existing}
    if set(data.stage_ids) != existing_ids:
        raise ConflictError("stage_ids must contain exactly the caller's stages")
    stages = await repo.reorder(user.id, data.stage_ids)
    return [PipelineStageRead.model_validate(s) for s in stages]
