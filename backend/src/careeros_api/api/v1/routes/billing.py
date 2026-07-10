"""Endpoints for billing and Stripe webhooks."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from careeros_api.api.deps import CurrentUserDep, SessionDep, require_plan
from careeros_api.core.billing import BillingProvider, get_billing_provider
from careeros_api.models.subscription import Subscription
from careeros_api.schemas.billing import (
    CheckoutRequest,
    CheckoutSessionOut,
    PortalRequest,
    PortalSessionOut,
    SubscriptionRead,
)
from careeros_api.services import billing as billing_service

router = APIRouter(tags=["billing"])

BillingProviderDep = Depends(get_billing_provider)
SubscriptionDep = Annotated[Subscription, Depends(require_plan("free"))]


@router.get("/billing/subscription", response_model=SubscriptionRead)
async def get_subscription(subscription: SubscriptionDep) -> SubscriptionRead:
    """Return the caller's subscription (creating a free row on first access)."""
    return SubscriptionRead.model_validate(subscription)


@router.post("/billing/checkout", response_model=CheckoutSessionOut)
async def create_checkout(
    session: SessionDep,
    current_user: CurrentUserDep,
    data: CheckoutRequest,
    provider: BillingProvider = BillingProviderDep,
) -> CheckoutSessionOut:
    """Start a checkout flow for the requested plan."""
    checkout = await billing_service.create_checkout(session, current_user, data, provider)
    return CheckoutSessionOut(id=checkout.id, url=checkout.url)


@router.post("/billing/portal", response_model=PortalSessionOut)
async def create_portal(
    session: SessionDep,
    current_user: CurrentUserDep,
    data: PortalRequest,
    provider: BillingProvider = BillingProviderDep,
) -> PortalSessionOut:
    """Open the billing customer portal."""
    portal = await billing_service.create_portal(session, current_user, data, provider)
    return PortalSessionOut(url=portal.url)


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    provider: BillingProvider = BillingProviderDep,
) -> Response:
    """Receive and acknowledge a Stripe webhook.

    The signature is verified when Stripe is configured; in noop/test mode the
    payload is accepted and a 200 is returned.
    """
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    await billing_service.handle_webhook(provider, payload=payload, signature=signature)
    return Response(status_code=status.HTTP_200_OK)
