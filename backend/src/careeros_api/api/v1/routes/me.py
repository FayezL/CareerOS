"""Endpoints for the authenticated user's own profile (``/api/v1/me``)."""

from __future__ import annotations

from fastapi import APIRouter

from careeros_api.api.deps import CurrentUserDep, SessionDep
from careeros_api.schemas.user import UserRead, UserUpdate
from careeros_api.services.user import update_user

router = APIRouter(prefix="/me", tags=["users"])


@router.get("", response_model=UserRead)
async def get_me(current_user: CurrentUserDep) -> UserRead:
    """Return the authenticated user's profile."""
    return UserRead.model_validate(current_user)


@router.patch("", response_model=UserRead)
async def update_me(
    data: UserUpdate,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> UserRead:
    """Update the authenticated user's mutable profile fields."""
    updated = await update_user(session, current_user, data)
    return UserRead.model_validate(updated)
