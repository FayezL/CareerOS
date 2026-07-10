"""Repository for the ``Note`` model (all reads scoped by ``user_id``)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import ColumnExpressionArgument, select
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.models.note import Note
from careeros_api.repositories.base import BaseRepository
from careeros_api.schemas.note import NoteCreate, NoteUpdate


class NoteRepository(BaseRepository[Note]):
    """Data access for notes belonging to a single user."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Note)

    async def list(  # type: ignore[override]
        self,
        user_id: uuid.UUID,
        *,
        limit: int,
        cursor: str | None = None,
        application_id: uuid.UUID | None = None,
        contact_id: uuid.UUID | None = None,
    ) -> tuple[Sequence[Note], str | None]:
        """Page through a user's non-deleted notes with optional filters."""

        def build_filters() -> list[ColumnExpressionArgument[bool]]:
            conditions: list[ColumnExpressionArgument[bool]] = [Note.deleted_at.is_(None)]
            if application_id is not None:
                conditions.append(Note.application_id == application_id)
            if contact_id is not None:
                conditions.append(Note.contact_id == contact_id)
            return conditions

        return await self.list_paginated(
            user_id,
            limit=limit,
            cursor=cursor,
            filters_builder=build_filters,
        )

    async def get(self, user_id: uuid.UUID, note_id: uuid.UUID) -> Note | None:
        """Return the note if it exists, belongs to ``user_id``, and is not deleted."""
        stmt = select(Note).where(
            Note.id == note_id,
            Note.user_id == user_id,
            Note.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, data: NoteCreate) -> Note:
        """Insert a new note owned by ``user_id``."""
        note = Note(user_id=user_id, **data.model_dump())
        self.session.add(note)
        await self.session.flush()
        await self.session.refresh(note)
        return note

    async def update(self, note: Note, data: NoteUpdate) -> Note:
        """Apply a partial update to ``note`` using only provided fields."""
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(note, field, value)
        await self.session.flush()
        await self.session.refresh(note)
        return note

    async def soft_delete(self, note: Note) -> None:
        """Mark ``note`` as deleted without removing the row."""
        note.deleted_at = datetime.now(tz=UTC)
        await self.session.flush()
