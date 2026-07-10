"""Repository for the ``PipelineStage`` model (all reads scoped by ``user_id``)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.models.application import Application
from careeros_api.models.pipeline_stage import PipelineStage
from careeros_api.repositories.base import BaseRepository
from careeros_api.schemas.pipeline import PipelineStageCreate, PipelineStageUpdate


class PipelineStageRepository(BaseRepository[PipelineStage]):
    """Data access for a user's pipeline stages."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, PipelineStage)

    async def list_ordered(self, user_id: uuid.UUID) -> Sequence[PipelineStage]:
        """Return the caller's stages ordered by ``position`` ascending."""
        stmt = (
            select(PipelineStage)
            .where(PipelineStage.user_id == user_id)
            .order_by(PipelineStage.position.asc(), PipelineStage.id.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get(self, user_id: uuid.UUID, stage_id: uuid.UUID) -> PipelineStage | None:
        """Return the stage if it exists and belongs to ``user_id``."""
        stmt = select(PipelineStage).where(
            PipelineStage.id == stage_id,
            PipelineStage.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count(self, user_id: uuid.UUID) -> int:
        """Number of stages owned by ``user_id``."""
        stmt = (
            select(func.count()).select_from(PipelineStage).where(PipelineStage.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create(self, user_id: uuid.UUID, data: PipelineStageCreate) -> PipelineStage:
        """Insert a new stage appended after the current maximum position."""
        stage = PipelineStage(
            user_id=user_id,
            name=data.name,
            color=data.color,
            position=await self._next_position(user_id),
        )
        self.session.add(stage)
        await self.session.flush()
        await self.session.refresh(stage)
        return stage

    async def update(self, stage: PipelineStage, data: PipelineStageUpdate) -> PipelineStage:
        """Apply a partial update to ``stage`` using only provided fields."""
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(stage, field, value)
        await self.session.flush()
        await self.session.refresh(stage)
        return stage

    async def delete(self, stage: PipelineStage) -> None:
        """Hard-delete ``stage`` (pipeline stages are not soft-deleted)."""
        await self.session.delete(stage)
        await self.session.flush()

    async def count_applications(self, stage_id: uuid.UUID) -> int:
        """Number of applications currently sitting on ``stage_id``."""
        stmt = (
            select(func.count())
            .select_from(Application)
            .where(Application.current_stage_id == stage_id)
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def reorder(
        self, user_id: uuid.UUID, stage_ids: Sequence[uuid.UUID]
    ) -> Sequence[PipelineStage]:
        """Renumber the caller's stages to ``0..n-1`` following ``stage_ids`` order.

        Positions are first moved to a high offset and flushed, so the
        ``(user_id, position)`` unique constraint cannot fire on intermediate
        values while renumbering.
        """
        stages = await self.list_ordered(user_id)
        by_id: dict[uuid.UUID, PipelineStage] = {s.id: s for s in stages}

        offset = len(stages) + 1000
        for stage in stages:
            stage.position = stage.position + offset
        await self.session.flush()

        for position, stage_id in enumerate(stage_ids):
            found = by_id.get(stage_id)
            if found is not None:
                found.position = position
        await self.session.flush()

        return await self.list_ordered(user_id)

    async def _next_position(self, user_id: uuid.UUID) -> int:
        stmt = select(func.max(PipelineStage.position)).where(PipelineStage.user_id == user_id)
        result = await self.session.execute(stmt)
        current = result.scalar_one()
        return (current or -1) + 1
