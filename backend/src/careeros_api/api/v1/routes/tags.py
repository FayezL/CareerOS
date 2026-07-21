"""Endpoints for the authenticated user's tags (``/api/v1/tags``).

Tags are the filtering/analytics axis (Remote, Visa Sponsorship, Python, …).
They are normally created inline from the application form (names auto-resolve
on create/update), but this route lets the picker list, add, and remove them.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Response, status

from careeros_api.api.deps import CurrentUserDep, SessionDep
from careeros_api.schemas.tag import TagCreate, TagRead
from careeros_api.services import tag as tag_service

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagRead])
async def list_tags(
    session: SessionDep,
    current_user: CurrentUserDep,
) -> list[TagRead]:
    """List the caller's tags, seeding the curated defaults on first access."""
    return await tag_service.list_tags(session, current_user)


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(
    session: SessionDep,
    current_user: CurrentUserDep,
    data: TagCreate,
) -> TagRead:
    """Create a tag explicitly (rejects a case-insensitive duplicate)."""
    return await tag_service.create_tag(session, current_user, data)


@router.delete("/{tag_id}")
async def delete_tag(
    session: SessionDep,
    current_user: CurrentUserDep,
    tag_id: uuid.UUID,
) -> Response:
    """Delete a tag owned by the caller (detaches it from all applications)."""
    await tag_service.delete_tag(session, current_user, tag_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
