"""Note business-logic services."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.errors import NotFoundError
from careeros_api.models.user import User
from careeros_api.repositories.note import NoteRepository
from careeros_api.schemas.common import PageOut
from careeros_api.schemas.note import NoteCreate, NoteRead, NoteUpdate


async def list_notes(
    session: AsyncSession,
    user: User,
    *,
    limit: int,
    cursor: str | None,
    application_id: uuid.UUID | None,
    contact_id: uuid.UUID | None,
) -> PageOut[NoteRead]:
    """Return one page of the caller's notes."""
    repo = NoteRepository(session)
    items, next_cursor = await repo.list(
        user.id,
        limit=limit,
        cursor=cursor,
        application_id=application_id,
        contact_id=contact_id,
    )
    return PageOut(items=[NoteRead.model_validate(n) for n in items], next_cursor=next_cursor)


async def get_note(session: AsyncSession, user: User, note_id: uuid.UUID) -> NoteRead:
    """Return a single note owned by the caller."""
    repo = NoteRepository(session)
    note = await repo.get(user.id, note_id)
    if note is None:
        raise NotFoundError(f"Note {note_id} not found")
    return NoteRead.model_validate(note)


async def create_note(session: AsyncSession, user: User, data: NoteCreate) -> NoteRead:
    """Create a new note for the caller."""
    repo = NoteRepository(session)
    note = await repo.create(user.id, data)
    return NoteRead.model_validate(note)


async def update_note(
    session: AsyncSession,
    user: User,
    note_id: uuid.UUID,
    data: NoteUpdate,
) -> NoteRead:
    """Partially update a note owned by the caller."""
    repo = NoteRepository(session)
    note = await repo.get(user.id, note_id)
    if note is None:
        raise NotFoundError(f"Note {note_id} not found")
    updated = await repo.update(note, data)
    return NoteRead.model_validate(updated)


async def delete_note(session: AsyncSession, user: User, note_id: uuid.UUID) -> None:
    """Soft-delete a note owned by the caller."""
    repo = NoteRepository(session)
    note = await repo.get(user.id, note_id)
    if note is None:
        raise NotFoundError(f"Note {note_id} not found")
    await repo.soft_delete(note)
