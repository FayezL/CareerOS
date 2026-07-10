"""Repository for the ``Subscription`` model (scoped by ``user_id``)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.models.subscription import Subscription
from careeros_api.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    """Data access for a user's subscription."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Subscription)

    async def get_or_create(self, user_id: uuid.UUID) -> Subscription:
        """Return the caller's subscription, creating a free one on first access."""
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.session.execute(stmt)
        subscription = result.scalar_one_or_none()
        if subscription is None:
            subscription = Subscription(user_id=user_id, plan="free", status="active")
            self.session.add(subscription)
            await self.session.flush()
            await self.session.refresh(subscription)
        return subscription

    async def get(self, user_id: uuid.UUID) -> Subscription | None:
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
