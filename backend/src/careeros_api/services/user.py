"""User-related services."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.core.security.clerk import CurrentUser
from careeros_api.models.user import User
from careeros_api.schemas.user import UserUpdate


async def get_or_create_user(session: AsyncSession, current: CurrentUser) -> User:
    """Return the local user row for ``current``, creating or refreshing it.

    The Clerk-issued JWT is the source of truth for mutable profile fields, so
    on every call we mirror ``email``/``full_name``/``avatar_url`` into the row.
    """
    result = await session.execute(select(User).where(User.clerk_user_id == current.clerk_user_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            clerk_user_id=current.clerk_user_id,
            email=current.email,
            full_name=current.full_name,
            avatar_url=current.avatar_url,
        )
        session.add(user)
    else:
        user.email = current.email
        user.full_name = current.full_name
        user.avatar_url = current.avatar_url

    await session.flush()
    await session.refresh(user)
    return user


async def update_user(session: AsyncSession, db_user: User, data: UserUpdate) -> User:
    """Apply a partial update to ``db_user`` using only the fields provided."""
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(db_user, field, value)

    await session.flush()
    await session.refresh(db_user)
    return db_user
