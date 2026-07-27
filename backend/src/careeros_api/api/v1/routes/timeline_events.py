"""Endpoints for the authenticated user's timeline events (``/api/v1/timeline-events``)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Response, status

from careeros_api.api.deps import CurrentUserDep, SessionDep
from careeros_api.schemas.timeline_event import (
    TimelineEventCreate,
    TimelineEventRead,
)
from careeros_api.services import timeline_event as timeline_event_service

router = APIRouter(prefix="/timeline-events", tags=["timeline-events"])


@router.get("", response_model=list[TimelineEventRead])
async def list_timeline_events(
    session: SessionDep,
    current_user: CurrentUserDep,
    application_id: uuid.UUID = Query(...),
) -> list[TimelineEventRead]:
    """List all timeline events for one application, oldest-first."""
    return await timeline_event_service.list_events(session, current_user, application_id)


@router.post(
    "",
    response_model=TimelineEventRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_timeline_event(
    session: SessionDep,
    current_user: CurrentUserDep,
    data: TimelineEventCreate,
) -> TimelineEventRead:
    """Create a new timeline event for the caller."""
    return await timeline_event_service.create_event(session, current_user, data)


@router.delete("/{event_id}")
async def delete_timeline_event(
    session: SessionDep,
    current_user: CurrentUserDep,
    event_id: uuid.UUID,
) -> Response:
    """Hard-delete a timeline event owned by the caller."""
    await timeline_event_service.delete_event(session, current_user, event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
