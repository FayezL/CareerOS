"""FastAPI dependencies shared across routers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.core.security.clerk import verify_clerk_jwt
from careeros_api.core.security.errors import AuthError
from careeros_api.db.session import get_session
from careeros_api.models.subscription import Subscription
from careeros_api.models.user import User
from careeros_api.repositories.subscription import SubscriptionRepository
from careeros_api.services.user import get_or_create_user

_BEARER_PREFIX = "Bearer "


async def get_current_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Verify the bearer JWT and return the upserted local ``User`` row."""
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith(_BEARER_PREFIX):
        raise AuthError("Missing or malformed Authorization header")

    token = authorization[len(_BEARER_PREFIX) :].strip()
    if not token:
        raise AuthError("Missing bearer token")

    current = await verify_clerk_jwt(token)
    return await get_or_create_user(session, current)


SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_plan(plan: str) -> Callable[[AsyncSession, User], Awaitable[Subscription]]:
    """Build a dependency that resolves the caller's subscription.

    v1 is intentionally permissive: the caller's plan is not enforced here. The
    dependency still materialises the subscription row (creating a free one on
    first access) so gated routes can rely on it and so the hook exists for a
    future enforcement point.
    """

    async def _dependency(
        session: SessionDep,
        current_user: CurrentUserDep,
    ) -> Subscription:
        # Permissive in v1: ``plan`` is intentionally not enforced here, but is
        # retained as the future enforcement point.
        _ = plan
        repo = SubscriptionRepository(session)
        return await repo.get_or_create(current_user.id)

    return _dependency
