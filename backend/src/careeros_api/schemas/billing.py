"""Billing/subscription request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Plan = Literal["free", "pro", "team"]


class SubscriptionRead(BaseModel):
    """Public representation of a user's subscription."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    plan: str
    status: str
    stripe_customer_id: str | None
    stripe_subscription_id: str | None
    current_period_end: datetime | None
    created_at: datetime
    updated_at: datetime


class CheckoutRequest(BaseModel):
    """Request to start a checkout flow for ``plan``."""

    plan: Plan = Field(..., description="Target plan / Stripe price identifier.")
    success_url: str = Field(..., max_length=2048)
    cancel_url: str = Field(..., max_length=2048)


class CheckoutSessionOut(BaseModel):
    """A checkout session returned to the client."""

    id: str
    url: str


class PortalRequest(BaseModel):
    """Request to open the billing portal."""

    return_url: str = Field(..., max_length=2048)


class PortalSessionOut(BaseModel):
    """A billing-portal session returned to the client."""

    url: str
