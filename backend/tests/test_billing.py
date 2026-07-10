"""Tests for billing endpoints (noop provider) and the Stripe webhook."""

from __future__ import annotations

from httpx import AsyncClient

from careeros_api.core.billing import NoopBillingProvider, get_billing_provider
from tests.helpers import AuthHeaders


def test_default_provider_is_noop_without_stripe_key() -> None:
    assert isinstance(get_billing_provider(), NoopBillingProvider)


async def test_subscription_is_created_on_first_access(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    response = await client.get("/api/v1/billing/subscription", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["plan"] == "free"
    assert body["status"] == "active"


async def test_checkout_returns_session_url(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    response = await client.post(
        "/api/v1/billing/checkout",
        headers=headers,
        json={
            "plan": "pro",
            "success_url": "https://app.example.com/success",
            "cancel_url": "https://app.example.com/cancel",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"]
    assert "success" in body["url"]

    subscription = await client.get("/api/v1/billing/subscription", headers=headers)
    assert subscription.json()["plan"] == "pro"


async def test_portal_returns_url(client: AsyncClient, auth: AuthHeaders, require_db: None) -> None:
    headers = auth()
    response = await client.post(
        "/api/v1/billing/portal",
        headers=headers,
        json={"return_url": "https://app.example.com/settings"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["url"]


async def test_stripe_webhook_returns_200_without_auth(client: AsyncClient) -> None:
    # The webhook is public and (in noop/test mode) accepts any payload.
    response = await client.post(
        "/api/v1/webhooks/stripe",
        content=b'{"type":"checkout.session.completed"}',
        headers={"stripe-signature": "test", "content-type": "application/json"},
    )
    assert response.status_code == 200
