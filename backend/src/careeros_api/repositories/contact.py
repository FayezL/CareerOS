"""Repository for the ``Contact`` model (all reads scoped by ``user_id``)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import ColumnExpressionArgument, select
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.models.contact import Contact
from careeros_api.repositories.base import BaseRepository
from careeros_api.schemas.contact import ContactCreate, ContactUpdate


class ContactRepository(BaseRepository[Contact]):
    """Data access for contacts belonging to a single user."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Contact)

    async def list(  # type: ignore[override]
        self,
        user_id: uuid.UUID,
        *,
        limit: int,
        cursor: str | None = None,
        company_id: uuid.UUID | None = None,
        q: str | None = None,
    ) -> tuple[Sequence[Contact], str | None]:
        """Page through a user's non-deleted contacts with optional filters."""

        def build_filters() -> list[ColumnExpressionArgument[bool]]:
            conditions: list[ColumnExpressionArgument[bool]] = [Contact.deleted_at.is_(None)]
            if company_id is not None:
                conditions.append(Contact.company_id == company_id)
            if q:
                conditions.append(
                    Contact.first_name.ilike(f"%{q}%")
                    | Contact.last_name.ilike(f"%{q}%")
                    | Contact.email.ilike(f"%{q}%")
                )
            return conditions

        return await self.list_paginated(
            user_id,
            limit=limit,
            cursor=cursor,
            filters_builder=build_filters,
        )

    async def get(self, user_id: uuid.UUID, contact_id: uuid.UUID) -> Contact | None:
        """Return the contact if it exists, belongs to ``user_id``, and is not deleted."""
        stmt = select(Contact).where(
            Contact.id == contact_id,
            Contact.user_id == user_id,
            Contact.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, data: ContactCreate) -> Contact:
        """Insert a new contact owned by ``user_id``."""
        contact = Contact(user_id=user_id, **data.model_dump())
        self.session.add(contact)
        await self.session.flush()
        await self.session.refresh(contact)
        return contact

    async def update(self, contact: Contact, data: ContactUpdate) -> Contact:
        """Apply a partial update to ``contact`` using only provided fields."""
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(contact, field, value)
        await self.session.flush()
        await self.session.refresh(contact)
        return contact

    async def soft_delete(self, contact: Contact) -> None:
        """Mark ``contact`` as deleted without removing the row."""
        contact.deleted_at = datetime.now(tz=UTC)
        await self.session.flush()
