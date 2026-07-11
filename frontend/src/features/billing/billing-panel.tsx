"use client"

import { useTransition } from "react"
import { toast } from "sonner"

import type { PlanTier, Subscription, SubscriptionStatus } from "@/types"
import { Badge, type BadgeProps } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/utils/cn"

import { openPortal, startCheckout } from "./actions"

type BillingPanelProps = {
  subscription: Subscription
  /** True when Stripe is not configured (noop/demo provider). */
  demo: boolean
}

type PlanDetails = {
  name: string
  price: string
  description: string
  features: string[]
}

const PLAN_DETAILS: Record<PlanTier, PlanDetails> = {
  free: {
    name: "Free",
    price: "$0",
    description: "Everything you need to start tracking your search.",
    features: ["Unlimited applications", "Pipeline Kanban", "Reminders & notes", "Basic analytics"],
  },
  pro: {
    name: "Pro",
    price: "$12/mo",
    description: "Advanced tools to move faster and land offers.",
    features: [
      "Everything in Free",
      "AI resume & cover-letter tools",
      "Advanced analytics",
      "Priority support",
    ],
  },
  team: {
    name: "Team",
    price: "Custom",
    description: "Collaboration and oversight for cohorts and teams.",
    features: ["Everything in Pro", "Shared workspaces", "Admin dashboard", "SSO & audit logs"],
  },
}

/** Plans surfaced as upgrade targets in the UI. */
const SHOP_PLANS: PlanTier[] = ["free", "pro"]

function statusVariant(status: SubscriptionStatus): BadgeProps["variant"] {
  switch (status) {
    case "active":
    case "trialing":
      return "default"
    case "past_due":
      return "destructive"
    default:
      return "outline"
  }
}

function formatPeriodEnd(value: string | null): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })
}

export function BillingPanel({ subscription, demo }: BillingPanelProps) {
  const [pending, startTransition] = useTransition()

  function handleUpgrade(plan: PlanTier) {
    startTransition(async () => {
      const res = await startCheckout(plan)
      if (!res.ok) {
        toast.error(res.error)
        return
      }
      if (res.demo) {
        toast.info("Billing is in demo mode until Stripe keys are configured.")
        return
      }
      toast.success("Redirecting to checkout…")
    })
  }

  function handlePortal() {
    startTransition(async () => {
      const res = await openPortal()
      if (!res.ok) {
        toast.error(res.error)
        return
      }
      if (res.demo) {
        toast.info("Billing is in demo mode until Stripe keys are configured.")
        return
      }
      toast.success("Opening the billing portal…")
    })
  }

  const details = PLAN_DETAILS[subscription.plan]

  return (
    <div className="space-y-8">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Billing</h1>
        <p className="text-sm text-muted-foreground">
          Manage your subscription, payment method, and invoices.
        </p>
      </div>

      {demo && (
        <p className="rounded-md border border-dashed border-border bg-muted/40 px-4 py-2 text-sm text-muted-foreground">
          Billing is in demo mode until Stripe keys are configured.
        </p>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Current plan</CardTitle>
          <CardDescription>Your subscription details and renewal date.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-x-8 gap-y-4">
          <div className="space-y-1">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Plan
            </p>
            <div className="flex items-center gap-2">
              <span className="text-lg font-semibold">{details.name}</span>
              <Badge variant={statusVariant(subscription.status)} className="capitalize">
                {subscription.status}
              </Badge>
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Current period ends
            </p>
            <p className="text-lg font-semibold">
              {formatPeriodEnd(subscription.current_period_end)}
            </p>
          </div>
          <Button variant="outline" onClick={handlePortal} disabled={pending} className="ml-auto">
            {pending ? "Loading…" : "Manage billing"}
          </Button>
        </CardContent>
      </Card>

      <div className="grid gap-6 sm:grid-cols-2">
        {SHOP_PLANS.map((plan) => {
          const planDetails = PLAN_DETAILS[plan]
          const current = subscription.plan === plan
          const isUpgrade = plan !== "free" && subscription.plan !== plan
          return (
            <Card
              key={plan}
              className={cn("flex flex-col", current && "border-primary ring-1 ring-primary")}
            >
              <CardHeader>
                <CardTitle>{planDetails.name}</CardTitle>
                <CardDescription>{planDetails.description}</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-1 flex-col gap-4">
                <p className="text-3xl font-semibold tracking-tight">{planDetails.price}</p>
                <ul className="flex-1 space-y-2 text-sm text-muted-foreground">
                  {planDetails.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2">
                      <span aria-hidden className="mt-0.5 text-primary">
                        •
                      </span>
                      {feature}
                    </li>
                  ))}
                </ul>
                <Button
                  onClick={() => handleUpgrade(plan)}
                  disabled={pending || current}
                  variant={current ? "secondary" : "default"}
                >
                  {current
                    ? "Current plan"
                    : isUpgrade
                      ? `Upgrade to ${planDetails.name}`
                      : `Switch to ${planDetails.name}`}
                </Button>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
