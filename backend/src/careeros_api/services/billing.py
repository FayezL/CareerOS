"""Billing/subscription business-logic services."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.core.billing import BillingProvider, CheckoutSession, PortalSession
from careeros_api.models.subscription import Subscription
from careeros_api.models.user import User
from careeros_api.repositories.subscription import SubscriptionRepository
from careeros_api.schemas.billing import CheckoutRequest, PortalRequest


async def get_subscription(session: AsyncSession, user: User) -> Subscription:
    """Return the caller's subscription, creating a free row on first access."""
    repo = SubscriptionRepository(session)
    return await repo.get_or_create(user.id)


async def create_checkout(
    session: AsyncSession,
    user: User,
    data: CheckoutRequest,
    provider: BillingProvider,
) -> CheckoutSession:
    """Start a checkout flow for ``data.plan`` via ``provider``."""
    repo = SubscriptionRepository(session)
    subscription = await repo.get_or_create(user.id)
    checkout = await provider.create_checkout_session(
        customer_email=user.email,
        plan=data.plan,
        success_url=data.success_url,
        cancel_url=data.cancel_url,
    )
    subscription.plan = data.plan
    await session.flush()
    return checkout


async def create_portal(
    session: AsyncSession,
    user: User,
    data: PortalRequest,
    provider: BillingProvider,
) -> PortalSession:
    """Open the billing portal via ``provider``."""
    repo = SubscriptionRepository(session)
    subscription = await repo.get_or_create(user.id)
    customer_id = subscription.stripe_customer_id or str(subscription.user_id)
    return await provider.create_portal_session(
        customer_id=customer_id,
        return_url=data.return_url,
    )


async def handle_webhook(provider: BillingProvider, *, payload: bytes, signature: str) -> None:
    """Verify (when Stripe is configured) and acknowledge a webhook event."""
    provider.construct_webhook_event(payload=payload, signature=signature)
