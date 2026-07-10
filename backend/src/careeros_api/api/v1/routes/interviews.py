"""Endpoints for the authenticated user's interviews (``/api/v1/interviews``)."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Query, Response, status

from careeros_api.api.deps import CurrentUserDep, SessionDep
from careeros_api.schemas.common import PageOut
from careeros_api.schemas.interview import InterviewCreate, InterviewRead, InterviewUpdate
from careeros_api.services import interview as interview_service

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.get("", response_model=PageOut[InterviewRead])
async def list_interviews(
    session: SessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    application_id: uuid.UUID | None = Query(None),
    from_at: datetime | None = Query(None, alias="from"),
    to_at: datetime | None = Query(None, alias="to"),
) -> PageOut[InterviewRead]:
    """Page through the caller's interviews with optional filters."""
    return await interview_service.list_interviews(
        session,
        current_user,
        limit=limit,
        cursor=cursor,
        application_id=application_id,
        from_at=from_at,
        to_at=to_at,
    )


@router.post("", response_model=InterviewRead, status_code=status.HTTP_201_CREATED)
async def create_interview(
    session: SessionDep,
    current_user: CurrentUserDep,
    data: InterviewCreate,
) -> InterviewRead:
    """Create a new interview for the caller."""
    return await interview_service.create_interview(session, current_user, data)


@router.get("/{interview_id}", response_model=InterviewRead)
async def get_interview(
    session: SessionDep,
    current_user: CurrentUserDep,
    interview_id: uuid.UUID,
) -> InterviewRead:
    """Return a single interview owned by the caller."""
    return await interview_service.get_interview(session, current_user, interview_id)


@router.patch("/{interview_id}", response_model=InterviewRead)
async def update_interview(
    session: SessionDep,
    current_user: CurrentUserDep,
    interview_id: uuid.UUID,
    data: InterviewUpdate,
) -> InterviewRead:
    """Partially update an interview owned by the caller."""
    return await interview_service.update_interview(session, current_user, interview_id, data)


@router.delete("/{interview_id}")
async def delete_interview(
    session: SessionDep,
    current_user: CurrentUserDep,
    interview_id: uuid.UUID,
) -> Response:
    """Soft-delete an interview owned by the caller."""
    await interview_service.delete_interview(session, current_user, interview_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
