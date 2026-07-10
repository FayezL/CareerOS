"""Application business-logic services."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.errors import NotFoundError
from careeros_api.models.user import User
from careeros_api.repositories.application import ApplicationRepository
from careeros_api.repositories.company import CompanyRepository
from careeros_api.repositories.pipeline import PipelineStageRepository
from careeros_api.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
)
from careeros_api.schemas.common import PageOut
from careeros_api.schemas.pipeline import MoveStageRequest, StageHistoryRead


async def list_applications(
    session: AsyncSession,
    user: User,
    *,
    limit: int,
    cursor: str | None,
    status: str | None,
    company_id: uuid.UUID | None,
    q: str | None,
) -> PageOut[ApplicationRead]:
    """Return one page of the caller's applications with companies embedded."""
    repo = ApplicationRepository(session)
    items, next_cursor = await repo.list(
        user.id,
        limit=limit,
        cursor=cursor,
        status=status,
        company_id=company_id,
        q=q,
    )
    return PageOut(
        items=[ApplicationRead.model_validate(a) for a in items],
        next_cursor=next_cursor,
    )


async def get_application(
    session: AsyncSession, user: User, application_id: uuid.UUID
) -> ApplicationRead:
    """Return a single application owned by the caller, with company embedded."""
    repo = ApplicationRepository(session)
    application = await repo.get(user.id, application_id)
    if application is None:
        raise NotFoundError(f"Application {application_id} not found")
    return ApplicationRead.model_validate(application)


async def create_application(
    session: AsyncSession, user: User, data: ApplicationCreate
) -> ApplicationRead:
    """Create a new application.

    The referenced ``company_id`` must belong to the caller; if it does not,
    a ``NotFoundError`` is raised so existence is never leaked.
    """
    company_repo = CompanyRepository(session)
    company = await company_repo.get(user.id, data.company_id)
    if company is None:
        raise NotFoundError(f"Company {data.company_id} not found")

    repo = ApplicationRepository(session)
    application = await repo.create(user.id, data)
    return ApplicationRead.model_validate(application)


async def update_application(
    session: AsyncSession,
    user: User,
    application_id: uuid.UUID,
    data: ApplicationUpdate,
) -> ApplicationRead:
    """Partially update an application owned by the caller."""
    repo = ApplicationRepository(session)
    application = await repo.get(user.id, application_id)
    if application is None:
        raise NotFoundError(f"Application {application_id} not found")
    updated = await repo.update(application, data)
    return ApplicationRead.model_validate(updated)


async def delete_application(session: AsyncSession, user: User, application_id: uuid.UUID) -> None:
    """Soft-delete an application owned by the caller."""
    repo = ApplicationRepository(session)
    application = await repo.get(user.id, application_id)
    if application is None:
        raise NotFoundError(f"Application {application_id} not found")
    await repo.soft_delete(application)


async def move_application(
    session: AsyncSession,
    user: User,
    application_id: uuid.UUID,
    data: MoveStageRequest,
) -> ApplicationRead:
    """Move an application to a different stage, recording the transition."""
    app_repo = ApplicationRepository(session)
    application = await app_repo.get(user.id, application_id)
    if application is None:
        raise NotFoundError(f"Application {application_id} not found")

    stage_repo = PipelineStageRepository(session)
    if await stage_repo.get(user.id, data.to_stage_id) is None:
        raise NotFoundError(f"Pipeline stage {data.to_stage_id} not found")

    moved = await app_repo.move(application, data.to_stage_id, data.note)
    return ApplicationRead.model_validate(moved)


async def list_application_history(
    session: AsyncSession, user: User, application_id: uuid.UUID
) -> list[StageHistoryRead]:
    """Return the stage-transition timeline for an application (oldest first)."""
    app_repo = ApplicationRepository(session)
    application = await app_repo.get(user.id, application_id)
    if application is None:
        raise NotFoundError(f"Application {application_id} not found")
    rows = await app_repo.history(application)
    return [StageHistoryRead.model_validate(row) for row in rows]
