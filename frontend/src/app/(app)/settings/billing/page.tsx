import type { Metadata } from "next"

import { apiFetch } from "@/lib/api-client"
import type { Subscription } from "@/lib/types"
import { ErrorState } from "@/components/error-state"
import { BillingPanel } from "@/features/billing/billing-panel"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Billing",
  description: "Manage your CareerOS subscription, payment method, and invoices.",
}

/**
 * Whether the backend is running in demo/noop mode. The noop provider never
 * links a Stripe customer or subscription, so the absence of both is a reliable
 * signal that Stripe keys are not configured.
 */
function isDemoMode(subscription: Subscription): boolean {
  return !subscription.stripe_customer_id && !subscription.stripe_subscription_id
}

export default async function BillingPage() {
  let subscription: Subscription | null = null
  let errorMessage: string | null = null

  try {
    subscription = await apiFetch<Subscription>("/billing/subscription")
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : "Unable to load billing right now."
  }

  if (!subscription) {
    return (
      <ErrorState
        title="Couldn't load billing"
        description={errorMessage ?? "Unable to load billing right now."}
      />
    )
  }

  return <BillingPanel subscription={subscription} demo={isDemoMode(subscription)} />
}
