"""Application business-logic services."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.errors import NotFoundError
from careeros_api.models.user import User
from careeros_api.repositories.application import ApplicationRepository
from careeros_api.repositories.company import CompanyRepository
from careeros_api.repositories.pipeline import PipelineStageRepository
from careeros_api.repositories.tag import TagRepository
from careeros_api.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
)
from careeros_api.schemas.common import PageOut
from careeros_api.schemas.company import CompanyCreate
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
    """Create a new application, resolving the company from the payload.

    The caller may pass either an existing ``company_id`` or a free-text
    ``company_name``. For a name, we reuse the caller's same-name company if one
    exists (case-insensitive) and otherwise create one inline — so the user
    never has to leave the application flow to manage companies. A bad
    ``company_id`` raises ``NotFoundError`` without leaking existence.
    """
    company_repo = CompanyRepository(session)
    if data.company_id is not None:
        company = await company_repo.get(user.id, data.company_id)
        if company is None:
            raise NotFoundError(f"Company {data.company_id} not found")
        company_id = company.id
    else:
        # data.company_name is guaranteed non-None by the schema validator.
        assert data.company_name is not None
        existing = await company_repo.get_by_name(user.id, data.company_name)
        if existing is not None:
            company_id = existing.id
        else:
            created = await company_repo.create(
                user.id,
                CompanyCreate(name=data.company_name),
            )
            company_id = created.id

    repo = ApplicationRepository(session)
    application = await repo.create(user.id, data, company_id=company_id)
    # Resolve tag names → Tag rows (creating as needed), then attach.
    if data.tags:
        tag_repo = TagRepository(session)
        tags = await tag_repo.resolve_names(user.id, data.tags)
        application.tags = tags
        await session.flush()
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
    # When tag names are supplied (even an empty list), replace the tag set.
    if data.tags is not None:
        tag_repo = TagRepository(session)
        updated.tags = await tag_repo.resolve_names(user.id, data.tags)
        await session.flush()
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
    """Move an application to a different stage, recording the transition.

    When the target stage's name is ``"Rejected"`` (case-insensitive) and the
    caller supplied rejection fields, they are written onto the application so
    analytics and the workspace timeline can surface them.
    """
    app_repo = ApplicationRepository(session)
    application = await app_repo.get(user.id, application_id)
    if application is None:
        raise NotFoundError(f"Application {application_id} not found")

    stage_repo = PipelineStageRepository(session)
    target_stage = await stage_repo.get(user.id, data.to_stage_id)
    if target_stage is None:
        raise NotFoundError(f"Pipeline stage {data.to_stage_id} not found")

    moved = await app_repo.move(application, data.to_stage_id, data.note)

    if target_stage.name.strip().lower() == "rejected":
        if data.rejection_reason_category is not None:
            moved.rejection_reason_category = data.rejection_reason_category
        if data.rejection_reason is not None:
            moved.rejection_reason = data.rejection_reason
        await session.flush()

    await session.refresh(moved, attribute_names=["company", "current_stage"])
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
