"use server"

import { headers } from "next/headers"
import { redirect } from "next/navigation"
import { revalidatePath } from "next/cache"

import { apiFetch } from "@/lib/api-client"
import type { CheckoutSession, PortalSession, PlanTier } from "@/lib/types"

export type ActionResult = { ok: boolean; demo?: boolean; error?: string }

function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) return error.message
  return "Something went wrong. Please try again."
}

/**
 * Resolve the request origin (scheme + host) from forwarded headers so we can
 * hand Stripe absolute success/cancel/return URLs. Falls back to localhost for
 * direct `next dev` access where proxies don't set forwarding headers.
 */
async function getOrigin(): Promise<string> {
  const h = await headers()
  const host = h.get("x-forwarded-host") ?? h.get("host") ?? "localhost:3000"
  const proto = h.get("x-forwarded-proto") ?? "http"
  return `${proto}://${host}`
}

/**
 * Whether `url` points away from our own origin and should be navigated to via
 * a client-facing redirect (real Stripe checkout/portal URLs). Same-origin or
 * relative URLs — as the noop provider returns — are treated as demo-mode
 * bounces and resolved in-place instead.
 */
function isExternalUrl(url: string, origin: string): boolean {
  try {
    const parsed = new URL(url, origin)
    return parsed.origin !== origin
  } catch {
    return false
  }
}

/**
 * Start a checkout flow for `plan`.
 *
 * When Stripe is configured the backend returns an external `checkout.stripe.com`
 * URL and we redirect to it. In demo/noop mode the backend echoes a same-origin
 * URL back; we simply revalidate and surface a demo notice instead of navigating.
 */
export async function startCheckout(plan: PlanTier): Promise<ActionResult> {
  const origin = await getOrigin()
  let session: CheckoutSession
  try {
    session = await apiFetch<CheckoutSession>("/billing/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        plan,
        success_url: `${origin}/settings/billing?checkout=success`,
        cancel_url: `${origin}/settings/billing?checkout=cancel`,
      }),
    })
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }

  if (isExternalUrl(session.url, origin)) {
    redirect(session.url)
  }

  revalidatePath("/settings/billing")
  return { ok: true, demo: true }
}

/**
 * Open the Stripe billing customer portal.
 *
 * With Stripe configured the backend returns an external portal URL and we
 * redirect to it. In demo/noop mode the provider echoes our return URL, so we
 * revalidate and return a demo notice instead.
 */
export async function openPortal(): Promise<ActionResult> {
  const origin = await getOrigin()
  let session: PortalSession
  try {
    session = await apiFetch<PortalSession>("/billing/portal", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ return_url: `${origin}/settings/billing` }),
    })
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }

  if (isExternalUrl(session.url, origin)) {
    redirect(session.url)
  }

  revalidatePath("/settings/billing")
  return { ok: true, demo: true }
}
