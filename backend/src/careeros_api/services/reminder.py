"""Reminder business-logic services."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.core.notifier import Notifier
from careeros_api.errors import NotFoundError
from careeros_api.models.user import User
from careeros_api.repositories.reminder import ReminderRepository
from careeros_api.schemas.common import PageOut
from careeros_api.schemas.reminder import (
    DispatchResult,
    ReminderCreate,
    ReminderRead,
    ReminderUpdate,
)


async def list_reminders(
    session: AsyncSession,
    user: User,
    *,
    limit: int,
    cursor: str | None,
    due_before: datetime | None,
    completed: bool | None,
) -> PageOut[ReminderRead]:
    """Return one page of the caller's reminders."""
    repo = ReminderRepository(session)
    items, next_cursor = await repo.list(
        user.id,
        limit=limit,
        cursor=cursor,
        due_before=due_before,
        completed=completed,
    )
    return PageOut(items=[ReminderRead.model_validate(r) for r in items], next_cursor=next_cursor)


async def get_reminder(session: AsyncSession, user: User, reminder_id: uuid.UUID) -> ReminderRead:
    """Return a single reminder owned by the caller."""
    repo = ReminderRepository(session)
    reminder = await repo.get(user.id, reminder_id)
    if reminder is None:
        raise NotFoundError(f"Reminder {reminder_id} not found")
    return ReminderRead.model_validate(reminder)


async def create_reminder(session: AsyncSession, user: User, data: ReminderCreate) -> ReminderRead:
    """Create a new reminder for the caller."""
    repo = ReminderRepository(session)
    reminder = await repo.create(user.id, data)
    return ReminderRead.model_validate(reminder)


async def update_reminder(
    session: AsyncSession,
    user: User,
    reminder_id: uuid.UUID,
    data: ReminderUpdate,
) -> ReminderRead:
    """Partially update a reminder owned by the caller."""
    repo = ReminderRepository(session)
    reminder = await repo.get(user.id, reminder_id)
    if reminder is None:
        raise NotFoundError(f"Reminder {reminder_id} not found")
    updated = await repo.update(reminder, data)
    return ReminderRead.model_validate(updated)


async def delete_reminder(session: AsyncSession, user: User, reminder_id: uuid.UUID) -> None:
    """Hard-delete a reminder owned by the caller."""
    repo = ReminderRepository(session)
    reminder = await repo.get(user.id, reminder_id)
    if reminder is None:
        raise NotFoundError(f"Reminder {reminder_id} not found")
    await repo.delete(reminder)


async def complete_reminder(
    session: AsyncSession, user: User, reminder_id: uuid.UUID
) -> ReminderRead:
    """Mark a reminder complete at the current time."""
    repo = ReminderRepository(session)
    reminder = await repo.get(user.id, reminder_id)
    if reminder is None:
        raise NotFoundError(f"Reminder {reminder_id} not found")
    completed = await repo.complete(reminder, datetime.now(tz=UTC))
    return ReminderRead.model_validate(completed)


async def snooze_reminder(
    session: AsyncSession,
    user: User,
    reminder_id: uuid.UUID,
    due_at: datetime,
) -> ReminderRead:
    """Push a reminder's ``due_at`` into the future."""
    repo = ReminderRepository(session)
    reminder = await repo.get(user.id, reminder_id)
    if reminder is None:
        raise NotFoundError(f"Reminder {reminder_id} not found")
    snoozed = await repo.set_due_at(reminder, due_at)
    return ReminderRead.model_validate(snoozed)


async def dispatch_due(session: AsyncSession, user: User, notifier: Notifier) -> DispatchResult:
    """Send all of the caller's due, pending reminders via ``notifier``."""
    repo = ReminderRepository(session)
    due = await repo.list_due(user.id, datetime.now(tz=UTC))
    for reminder in due:
        await notifier.send(
            to=getattr(user, "email", None),
            title=reminder.title,
            due_at=reminder.due_at,
            detail=None,
        )
    return DispatchResult(dispatched=len(due))
