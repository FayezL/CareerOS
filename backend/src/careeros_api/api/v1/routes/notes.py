"""Endpoints for the authenticated user's notes (``/api/v1/notes``)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Response, status

from careeros_api.api.deps import CurrentUserDep, SessionDep
from careeros_api.schemas.common import PageOut
from careeros_api.schemas.note import NoteCreate, NoteRead, NoteUpdate
from careeros_api.services import note as note_service

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=PageOut[NoteRead])
async def list_notes(
    session: SessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    application_id: uuid.UUID | None = Query(None),
    contact_id: uuid.UUID | None = Query(None),
) -> PageOut[NoteRead]:
    """Page through the caller's notes with optional filters."""
    return await note_service.list_notes(
        session,
        current_user,
        limit=limit,
        cursor=cursor,
        application_id=application_id,
        contact_id=contact_id,
    )


@router.post("", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note(
    session: SessionDep,
    current_user: CurrentUserDep,
    data: NoteCreate,
) -> NoteRead:
    """Create a new note for the caller."""
    return await note_service.create_note(session, current_user, data)


@router.get("/{note_id}", response_model=NoteRead)
async def get_note(
    session: SessionDep,
    current_user: CurrentUserDep,
    note_id: uuid.UUID,
) -> NoteRead:
    """Return a single note owned by the caller."""
    return await note_service.get_note(session, current_user, note_id)


@router.patch("/{note_id}", response_model=NoteRead)
async def update_note(
    session: SessionDep,
    current_user: CurrentUserDep,
    note_id: uuid.UUID,
    data: NoteUpdate,
) -> NoteRead:
    """Partially update a note owned by the caller."""
    return await note_service.update_note(session, current_user, note_id, data)


@router.delete("/{note_id}")
async def delete_note(
    session: SessionDep,
    current_user: CurrentUserDep,
    note_id: uuid.UUID,
) -> Response:
    """Soft-delete a note owned by the caller."""
    await note_service.delete_note(session, current_user, note_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
