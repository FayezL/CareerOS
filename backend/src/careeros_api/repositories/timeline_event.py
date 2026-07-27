"""Repository for the ``TimelineEvent`` model (all reads scoped by ``user_id``)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.models.timeline_event import TimelineEvent
from careeros_api.repositories.base import BaseRepository
from careeros_api.schemas.timeline_event import TimelineEventCreate


class TimelineEventRepository(BaseRepository[TimelineEvent]):
    """Data access for timeline events belonging to a single user."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TimelineEvent)

    async def list_for_application(
        self, user_id: uuid.UUID, application_id: uuid.UUID
    ) -> Sequence[TimelineEvent]:
        """All events for one application, oldest-first (narrative order)."""
        stmt = (
            select(TimelineEvent)
            .where(
                TimelineEvent.user_id == user_id,
                TimelineEvent.application_id == application_id,
            )
            .order_by(
                TimelineEvent.occurred_at.asc(),
                TimelineEvent.id.asc(),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get(self, user_id: uuid.UUID, event_id: uuid.UUID) -> TimelineEvent | None:
        """Return the event if it exists and belongs to ``user_id``."""
        stmt = select(TimelineEvent).where(
            TimelineEvent.id == event_id,
            TimelineEvent.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, data: TimelineEventCreate) -> TimelineEvent:
        """Insert a new timeline event owned by ``user_id``."""
        payload = data.model_dump(exclude={"rejection_reason_category"})
        event = TimelineEvent(user_id=user_id, **payload)
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def delete(self, event: TimelineEvent) -> None:
        """Hard-delete ``event`` — TimelineEvent has no SoftDeleteMixin."""
        await self.session.delete(event)
        await self.session.flush()
