"""Endpoints for the authenticated user's applications (``/api/v1/applications``)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Response, status

from careeros_api.api.deps import CurrentUserDep, SessionDep
from careeros_api.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationStatus,
    ApplicationUpdate,
)
from careeros_api.schemas.common import PageOut
from careeros_api.schemas.pipeline import MoveStageRequest, StageHistoryRead
from careeros_api.services import application as application_service

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=PageOut[ApplicationRead])
async def list_applications(
    session: SessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    status_filter: ApplicationStatus | None = Query(None, alias="status"),
    company_id: uuid.UUID | None = Query(None),
    q: str | None = Query(None),
) -> PageOut[ApplicationRead]:
    """Page through the caller's applications with optional filters."""
    return await application_service.list_applications(
        session,
        current_user,
        limit=limit,
        cursor=cursor,
        status=status_filter,
        company_id=company_id,
        q=q,
    )


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(
    session: SessionDep,
    current_user: CurrentUserDep,
    data: ApplicationCreate,
) -> ApplicationRead:
    """Create a new application for the caller."""
    return await application_service.create_application(session, current_user, data)


@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application(
    session: SessionDep,
    current_user: CurrentUserDep,
    application_id: uuid.UUID,
) -> ApplicationRead:
    """Return a single application owned by the caller, with company embedded."""
    return await application_service.get_application(session, current_user, application_id)


@router.patch("/{application_id}", response_model=ApplicationRead)
async def update_application(
    session: SessionDep,
    current_user: CurrentUserDep,
    application_id: uuid.UUID,
    data: ApplicationUpdate,
) -> ApplicationRead:
    """Partially update an application owned by the caller."""
    return await application_service.update_application(session, current_user, application_id, data)


@router.delete("/{application_id}")
async def delete_application(
    session: SessionDep,
    current_user: CurrentUserDep,
    application_id: uuid.UUID,
) -> Response:
    """Soft-delete an application owned by the caller."""
    await application_service.delete_application(session, current_user, application_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{application_id}/move", response_model=ApplicationRead)
async def move_application(
    session: SessionDep,
    current_user: CurrentUserDep,
    application_id: uuid.UUID,
    data: MoveStageRequest,
) -> ApplicationRead:
    """Move an application to a different pipeline stage."""
    return await application_service.move_application(session, current_user, application_id, data)


@router.get("/{application_id}/history", response_model=list[StageHistoryRead])
async def list_application_history(
    session: SessionDep,
    current_user: CurrentUserDep,
    application_id: uuid.UUID,
) -> list[StageHistoryRead]:
    """Return the stage-transition timeline for an application (oldest first)."""
    return await application_service.list_application_history(session, current_user, application_id)
