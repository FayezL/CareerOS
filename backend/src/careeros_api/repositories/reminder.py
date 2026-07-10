"""Repository for the ``Reminder`` model (all reads scoped by ``user_id``)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import ColumnExpressionArgument, select
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.models.reminder import Reminder
from careeros_api.repositories.base import BaseRepository
from careeros_api.schemas.reminder import ReminderCreate, ReminderUpdate


class ReminderRepository(BaseRepository[Reminder]):
    """Data access for reminders belonging to a single user."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Reminder)

    async def list(  # type: ignore[override]
        self,
        user_id: uuid.UUID,
        *,
        limit: int,
        cursor: str | None = None,
        due_before: datetime | None = None,
        completed: bool | None = None,
    ) -> tuple[Sequence[Reminder], str | None]:
        """Page through a user's reminders with optional filters."""

        def build_filters() -> list[ColumnExpressionArgument[bool]]:
            conditions: list[ColumnExpressionArgument[bool]] = []
            if due_before is not None:
                conditions.append(Reminder.due_at <= due_before)
            if completed is not None:
                if completed:
                    conditions.append(Reminder.completed_at.is_not(None))
                else:
                    conditions.append(Reminder.completed_at.is_(None))
            return conditions

        return await self.list_paginated(
            user_id,
            limit=limit,
            cursor=cursor,
            filters_builder=build_filters,
        )

    async def get(self, user_id: uuid.UUID, reminder_id: uuid.UUID) -> Reminder | None:
        """Return the reminder if it exists and belongs to ``user_id``."""
        stmt = select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, data: ReminderCreate) -> Reminder:
        """Insert a new reminder owned by ``user_id``."""
        reminder = Reminder(
            user_id=user_id,
            application_id=data.application_id,
            interview_id=data.interview_id,
            title=data.title,
            due_at=data.due_at,
        )
        self.session.add(reminder)
        await self.session.flush()
        await self.session.refresh(reminder)
        return reminder

    async def update(self, reminder: Reminder, data: ReminderUpdate) -> Reminder:
        """Apply a partial update to ``reminder`` using only provided fields."""
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(reminder, field, value)
        await self.session.flush()
        await self.session.refresh(reminder)
        return reminder

    async def set_due_at(self, reminder: Reminder, due_at: datetime) -> Reminder:
        """Snooze: push ``reminder``'s ``due_at`` to ``due_at``."""
        reminder.due_at = due_at
        await self.session.flush()
        await self.session.refresh(reminder)
        return reminder

    async def complete(self, reminder: Reminder, completed_at: datetime) -> Reminder:
        """Mark ``reminder`` as complete at ``completed_at``."""
        reminder.completed_at = completed_at
        await self.session.flush()
        await self.session.refresh(reminder)
        return reminder

    async def list_due(self, user_id: uuid.UUID, now: datetime) -> Sequence[Reminder]:
        """Return the caller's pending reminders due at or before ``now``."""
        stmt = (
            select(Reminder)
            .where(
                Reminder.user_id == user_id,
                Reminder.completed_at.is_(None),
                Reminder.due_at <= now,
            )
            .order_by(Reminder.due_at.asc(), Reminder.id.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete(self, reminder: Reminder) -> None:
        """Hard-delete ``reminder`` (reminders have no soft-delete)."""
        await self.session.delete(reminder)
        await self.session.flush()
