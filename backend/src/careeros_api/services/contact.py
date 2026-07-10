"""Contact business-logic services."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.errors import NotFoundError
from careeros_api.models.user import User
from careeros_api.repositories.contact import ContactRepository
from careeros_api.schemas.common import PageOut
from careeros_api.schemas.contact import ContactCreate, ContactRead, ContactUpdate


async def list_contacts(
    session: AsyncSession,
    user: User,
    *,
    limit: int,
    cursor: str | None,
    company_id: uuid.UUID | None,
    q: str | None,
) -> PageOut[ContactRead]:
    """Return one page of the caller's contacts."""
    repo = ContactRepository(session)
    items, next_cursor = await repo.list(
        user.id, limit=limit, cursor=cursor, company_id=company_id, q=q
    )
    return PageOut(items=[ContactRead.model_validate(c) for c in items], next_cursor=next_cursor)


async def get_contact(session: AsyncSession, user: User, contact_id: uuid.UUID) -> ContactRead:
    """Return a single contact owned by the caller."""
    repo = ContactRepository(session)
    contact = await repo.get(user.id, contact_id)
    if contact is None:
        raise NotFoundError(f"Contact {contact_id} not found")
    return ContactRead.model_validate(contact)


async def create_contact(session: AsyncSession, user: User, data: ContactCreate) -> ContactRead:
    """Create a new contact for the caller."""
    repo = ContactRepository(session)
    contact = await repo.create(user.id, data)
    return ContactRead.model_validate(contact)


async def update_contact(
    session: AsyncSession,
    user: User,
    contact_id: uuid.UUID,
    data: ContactUpdate,
) -> ContactRead:
    """Partially update a contact owned by the caller."""
    repo = ContactRepository(session)
    contact = await repo.get(user.id, contact_id)
    if contact is None:
        raise NotFoundError(f"Contact {contact_id} not found")
    updated = await repo.update(contact, data)
    return ContactRead.model_validate(updated)


async def delete_contact(session: AsyncSession, user: User, contact_id: uuid.UUID) -> None:
    """Soft-delete a contact owned by the caller."""
    repo = ContactRepository(session)
    contact = await repo.get(user.id, contact_id)
    if contact is None:
        raise NotFoundError(f"Contact {contact_id} not found")
    await repo.soft_delete(contact)
