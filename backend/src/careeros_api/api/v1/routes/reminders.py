"""Endpoints for the authenticated user's reminders (``/api/v1/reminders``)."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Query, Response, status

from careeros_api.api.deps import CurrentUserDep, SessionDep
from careeros_api.core.notifier import get_notifier
from careeros_api.schemas.common import PageOut
from careeros_api.schemas.reminder import (
    DispatchResult,
    ReminderCreate,
    ReminderRead,
    ReminderUpdate,
    SnoozeRequest,
)
from careeros_api.services import reminder as reminder_service

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", response_model=PageOut[ReminderRead])
async def list_reminders(
    session: SessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    due_before: datetime | None = Query(None),
    completed: bool | None = Query(None),
) -> PageOut[ReminderRead]:
    """Page through the caller's reminders with optional filters."""
    return await reminder_service.list_reminders(
        session,
        current_user,
        limit=limit,
        cursor=cursor,
        due_before=due_before,
        completed=completed,
    )


@router.post("", response_model=ReminderRead, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    session: SessionDep,
    current_user: CurrentUserDep,
    data: ReminderCreate,
) -> ReminderRead:
    """Create a new reminder for the caller."""
    return await reminder_service.create_reminder(session, current_user, data)


@router.get("/{reminder_id}", response_model=ReminderRead)
async def get_reminder(
    session: SessionDep,
    current_user: CurrentUserDep,
    reminder_id: uuid.UUID,
) -> ReminderRead:
    """Return a single reminder owned by the caller."""
    return await reminder_service.get_reminder(session, current_user, reminder_id)


@router.patch("/{reminder_id}", response_model=ReminderRead)
async def update_reminder(
    session: SessionDep,
    current_user: CurrentUserDep,
    reminder_id: uuid.UUID,
    data: ReminderUpdate,
) -> ReminderRead:
    """Partially update a reminder owned by the caller."""
    return await reminder_service.update_reminder(session, current_user, reminder_id, data)


@router.delete("/{reminder_id}")
async def delete_reminder(
    session: SessionDep,
    current_user: CurrentUserDep,
    reminder_id: uuid.UUID,
) -> Response:
    """Delete a reminder owned by the caller."""
    await reminder_service.delete_reminder(session, current_user, reminder_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{reminder_id}/complete", response_model=ReminderRead)
async def complete_reminder(
    session: SessionDep,
    current_user: CurrentUserDep,
    reminder_id: uuid.UUID,
) -> ReminderRead:
    """Mark a reminder complete."""
    return await reminder_service.complete_reminder(session, current_user, reminder_id)


@router.post("/{reminder_id}/snooze", response_model=ReminderRead)
async def snooze_reminder(
    session: SessionDep,
    current_user: CurrentUserDep,
    reminder_id: uuid.UUID,
    data: SnoozeRequest,
) -> ReminderRead:
    """Push a reminder's ``due_at`` into the future."""
    return await reminder_service.snooze_reminder(session, current_user, reminder_id, data.due_at)


@router.post("/dispatch-due", response_model=DispatchResult)
async def dispatch_due(session: SessionDep, current_user: CurrentUserDep) -> DispatchResult:
    """Send all of the caller's due, pending reminders (dev/utility endpoint)."""
    return await reminder_service.dispatch_due(session, current_user, get_notifier())
