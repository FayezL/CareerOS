"""Billing-provider abstraction.

* ``NoopBillingProvider`` — returns stub sessions (selected when no Stripe key
  is configured; used in tests/local dev).
* ``StripeBillingProvider`` — uses the ``stripe`` library, imported lazily so a
  missing dependency or credentials never breaks application import.

``get_billing_provider()`` selects one based on settings.
"""

from __future__ import annotations

from dataclasses import dataclass

from careeros_api.core.config import settings


@dataclass(frozen=True)
class CheckoutSession:
    """A checkout session handle returned to the client."""

    id: str
    url: str


@dataclass(frozen=True)
class PortalSession:
    """A billing-portal session handle returned to the client."""

    url: str


class BillingProvider:
    """Abstract interface for checkout, portal, and webhook handling."""

    async def create_checkout_session(
        self, *, customer_email: str, plan: str, success_url: str, cancel_url: str
    ) -> CheckoutSession:
        raise NotImplementedError

    async def create_portal_session(self, *, customer_id: str, return_url: str) -> PortalSession:
        raise NotImplementedError

    def construct_webhook_event(self, *, payload: bytes, signature: str) -> object:
        """Verify and parse a Stripe webhook payload; ``object`` on success."""
        raise NotImplementedError


class NoopBillingProvider(BillingProvider):
    """Stub provider that returns deterministic placeholder sessions."""

    async def create_checkout_session(
        self, *, customer_email: str, plan: str, success_url: str, cancel_url: str
    ) -> CheckoutSession:
        return CheckoutSession(
            id=f"noop_cs_{plan}",
            url=f"{success_url}?session_id=noop_cs_{plan}&plan={plan}",
        )

    async def create_portal_session(self, *, customer_id: str, return_url: str) -> PortalSession:
        del customer_id
        return PortalSession(url=return_url)

    def construct_webhook_event(self, *, payload: bytes, signature: str) -> object:
        # In test/noop mode there is no signature to verify; accept and echo.
        import json

        del signature
        try:
            return json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {"raw": payload.decode("utf-8", errors="replace")}


class StripeBillingProvider(BillingProvider):
    """Stripe-backed provider (``stripe`` imported lazily)."""

    def __init__(self, secret_key: str, webhook_secret: str) -> None:
        self.secret_key = secret_key
        self.webhook_secret = webhook_secret

    async def create_checkout_session(
        self, *, customer_email: str, plan: str, success_url: str, cancel_url: str
    ) -> CheckoutSession:
        import stripe

        stripe.api_key = self.secret_key
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer_email=customer_email,
            line_items=[{"price": plan, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return CheckoutSession(id=str(session.id), url=str(session.url))

    async def create_portal_session(self, *, customer_id: str, return_url: str) -> PortalSession:
        import stripe

        stripe.api_key = self.secret_key
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return PortalSession(url=str(session.url))

    def construct_webhook_event(self, *, payload: bytes, signature: str) -> object:
        import stripe

        return stripe.Webhook.construct_event(  # type: ignore[no-untyped-call]
            payload=payload,
            sig_header=signature,
            secret=self.webhook_secret,
        )


def get_billing_provider() -> BillingProvider:
    """Return the configured billing provider (noop when Stripe is unset)."""
    secret_key = getattr(settings, "STRIPE_SECRET_KEY", None)
    if secret_key:
        webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "") or ""
        return StripeBillingProvider(secret_key, webhook_secret)
    return NoopBillingProvider()
