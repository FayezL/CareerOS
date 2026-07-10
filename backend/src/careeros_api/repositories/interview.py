"""Repository for the ``Interview`` model (all reads scoped by ``user_id``)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import ColumnExpressionArgument, select
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.models.interview import Interview
from careeros_api.repositories.base import BaseRepository
from careeros_api.schemas.interview import InterviewCreate, InterviewUpdate


class InterviewRepository(BaseRepository[Interview]):
    """Data access for interviews belonging to a single user."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Interview)

    async def list(  # type: ignore[override]
        self,
        user_id: uuid.UUID,
        *,
        limit: int,
        cursor: str | None = None,
        application_id: uuid.UUID | None = None,
        from_at: datetime | None = None,
        to_at: datetime | None = None,
    ) -> tuple[Sequence[Interview], str | None]:
        """Page through a user's non-deleted interviews with optional filters."""

        def build_filters() -> list[ColumnExpressionArgument[bool]]:
            conditions: list[ColumnExpressionArgument[bool]] = [Interview.deleted_at.is_(None)]
            if application_id is not None:
                conditions.append(Interview.application_id == application_id)
            if from_at is not None:
                conditions.append(Interview.scheduled_at >= from_at)
            if to_at is not None:
                conditions.append(Interview.scheduled_at <= to_at)
            return conditions

        return await self.list_paginated(
            user_id,
            limit=limit,
            cursor=cursor,
            filters_builder=build_filters,
        )

    async def get(self, user_id: uuid.UUID, interview_id: uuid.UUID) -> Interview | None:
        """Return the interview if it exists, belongs to ``user_id``, and is not deleted."""
        stmt = select(Interview).where(
            Interview.id == interview_id,
            Interview.user_id == user_id,
            Interview.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, data: InterviewCreate) -> Interview:
        """Insert a new interview owned by ``user_id``."""
        interview = Interview(user_id=user_id, **data.model_dump())
        self.session.add(interview)
        await self.session.flush()
        await self.session.refresh(interview)
        return interview

    async def update(self, interview: Interview, data: InterviewUpdate) -> Interview:
        """Apply a partial update to ``interview`` using only provided fields."""
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(interview, field, value)
        await self.session.flush()
        await self.session.refresh(interview)
        return interview

    async def soft_delete(self, interview: Interview) -> None:
        """Mark ``interview`` as deleted without removing the row."""
        interview.deleted_at = datetime.now(tz=UTC)
        await self.session.flush()
