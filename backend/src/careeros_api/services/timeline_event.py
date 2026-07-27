"""Timeline event business-logic services."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.errors import NotFoundError
from careeros_api.models.timeline_event import TimelineEventType
from careeros_api.models.user import User
from careeros_api.repositories.application import ApplicationRepository
from careeros_api.repositories.timeline_event import TimelineEventRepository
from careeros_api.schemas.timeline_event import (
    TimelineEventCreate,
    TimelineEventRead,
)


async def list_events(
    session: AsyncSession,
    user: User,
    application_id: uuid.UUID,
) -> list[TimelineEventRead]:
    """Return all timeline events for one application, oldest-first."""
    repo = TimelineEventRepository(session)
    events = await repo.list_for_application(user.id, application_id)
    return [TimelineEventRead.model_validate(e) for e in events]


async def create_event(
    session: AsyncSession,
    user: User,
    data: TimelineEventCreate,
) -> TimelineEventRead:
    """Create a timeline event for the caller.

    Validates that the application belongs to the user (raises
    ``NotFoundError`` otherwise, to avoid leaking existence). When the event
    type is ``REJECTED`` and a reason category is provided, the application's
    rejection fields are updated so analytics can aggregate them.
    """
    app_repo = ApplicationRepository(session)
    application = await app_repo.get(user.id, data.application_id)
    if application is None:
        raise NotFoundError(f"Application {data.application_id} not found")

    repo = TimelineEventRepository(session)
    event = await repo.create(user.id, data)

    if data.event_type == TimelineEventType.REJECTED and data.rejection_reason_category is not None:
        application.rejection_reason_category = data.rejection_reason_category
        if data.summary:
            application.rejection_reason = data.summary
        await session.flush()

    return TimelineEventRead.model_validate(event)


async def delete_event(
    session: AsyncSession,
    user: User,
    event_id: uuid.UUID,
) -> None:
    """Hard-delete a timeline event owned by the caller."""
    repo = TimelineEventRepository(session)
    event = await repo.get(user.id, event_id)
    if event is None:
        raise NotFoundError(f"Timeline event {event_id} not found")
    await repo.delete(event)
