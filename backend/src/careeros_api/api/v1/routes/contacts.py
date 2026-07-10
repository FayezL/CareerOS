"""Endpoints for the authenticated user's contacts (``/api/v1/contacts``)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Response, status

from careeros_api.api.deps import CurrentUserDep, SessionDep
from careeros_api.schemas.common import PageOut
from careeros_api.schemas.contact import ContactCreate, ContactRead, ContactUpdate
from careeros_api.services import contact as contact_service

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=PageOut[ContactRead])
async def list_contacts(
    session: SessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    company_id: uuid.UUID | None = Query(None),
    q: str | None = Query(None),
) -> PageOut[ContactRead]:
    """Page through the caller's contacts with optional filters."""
    return await contact_service.list_contacts(
        session, current_user, limit=limit, cursor=cursor, company_id=company_id, q=q
    )


@router.post("", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def create_contact(
    session: SessionDep,
    current_user: CurrentUserDep,
    data: ContactCreate,
) -> ContactRead:
    """Create a new contact for the caller."""
    return await contact_service.create_contact(session, current_user, data)


@router.get("/{contact_id}", response_model=ContactRead)
async def get_contact(
    session: SessionDep,
    current_user: CurrentUserDep,
    contact_id: uuid.UUID,
) -> ContactRead:
    """Return a single contact owned by the caller."""
    return await contact_service.get_contact(session, current_user, contact_id)


@router.patch("/{contact_id}", response_model=ContactRead)
async def update_contact(
    session: SessionDep,
    current_user: CurrentUserDep,
    contact_id: uuid.UUID,
    data: ContactUpdate,
) -> ContactRead:
    """Partially update a contact owned by the caller."""
    return await contact_service.update_contact(session, current_user, contact_id, data)


@router.delete("/{contact_id}")
async def delete_contact(
    session: SessionDep,
    current_user: CurrentUserDep,
    contact_id: uuid.UUID,
) -> Response:
    """Soft-delete a contact owned by the caller."""
    await contact_service.delete_contact(session, current_user, contact_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
