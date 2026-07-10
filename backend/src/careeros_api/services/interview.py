"""Interview business-logic services."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.errors import NotFoundError
from careeros_api.models.user import User
from careeros_api.repositories.application import ApplicationRepository
from careeros_api.repositories.interview import InterviewRepository
from careeros_api.schemas.common import PageOut
from careeros_api.schemas.interview import InterviewCreate, InterviewRead, InterviewUpdate


async def list_interviews(
    session: AsyncSession,
    user: User,
    *,
    limit: int,
    cursor: str | None,
    application_id: uuid.UUID | None,
    from_at: datetime | None,
    to_at: datetime | None,
) -> PageOut[InterviewRead]:
    """Return one page of the caller's interviews."""
    repo = InterviewRepository(session)
    items, next_cursor = await repo.list(
        user.id,
        limit=limit,
        cursor=cursor,
        application_id=application_id,
        from_at=from_at,
        to_at=to_at,
    )
    return PageOut(items=[InterviewRead.model_validate(i) for i in items], next_cursor=next_cursor)


async def get_interview(
    session: AsyncSession, user: User, interview_id: uuid.UUID
) -> InterviewRead:
    """Return a single interview owned by the caller."""
    repo = InterviewRepository(session)
    interview = await repo.get(user.id, interview_id)
    if interview is None:
        raise NotFoundError(f"Interview {interview_id} not found")
    return InterviewRead.model_validate(interview)


async def create_interview(
    session: AsyncSession, user: User, data: InterviewCreate
) -> InterviewRead:
    """Create a new interview for the caller.

    The referenced ``application_id`` must belong to the caller; if it does not,
    a ``NotFoundError`` is raised so existence is never leaked.
    """
    app_repo = ApplicationRepository(session)
    if await app_repo.get(user.id, data.application_id) is None:
        raise NotFoundError(f"Application {data.application_id} not found")

    repo = InterviewRepository(session)
    interview = await repo.create(user.id, data)
    return InterviewRead.model_validate(interview)


async def update_interview(
    session: AsyncSession,
    user: User,
    interview_id: uuid.UUID,
    data: InterviewUpdate,
) -> InterviewRead:
    """Partially update an interview owned by the caller."""
    repo = InterviewRepository(session)
    interview = await repo.get(user.id, interview_id)
    if interview is None:
        raise NotFoundError(f"Interview {interview_id} not found")
    updated = await repo.update(interview, data)
    return InterviewRead.model_validate(updated)


async def delete_interview(session: AsyncSession, user: User, interview_id: uuid.UUID) -> None:
    """Soft-delete an interview owned by the caller."""
    repo = InterviewRepository(session)
    interview = await repo.get(user.id, interview_id)
    if interview is None:
        raise NotFoundError(f"Interview {interview_id} not found")
    await repo.soft_delete(interview)
