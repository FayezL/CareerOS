import type { Metadata } from "next"
import Link from "next/link"
import { ArrowRight, Bell, ClipboardList, Clock, TrendingUp } from "lucide-react"

import { getAnalyticsSummary, listApplications, listReminders } from "@/services/api-client"
import type { AnalyticsSummary, Application, Reminder } from "@/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ErrorState } from "@/components/error-state"
import { ApplicationStatusBadge } from "@/features/applications/status-badge"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Dashboard",
  description: "How is your job search going today?",
}

export default async function DashboardPage() {
  let summary: AnalyticsSummary | null = null
  let applications: Application[] = []
  let reminders: Reminder[] = []
  let errorMessage: string | null = null

  try {
    summary = await getAnalyticsSummary()
  } catch (error) {
    errorMessage =
      error instanceof Error ? error.message : "Unable to load your dashboard right now."
  }

  if (summary) {
    // Recent activity + follow-ups are non-fatal.
    try {
      applications = (await listApplications()).slice(0, 6)
    } catch {
      // empty activity feed
    }
    try {
      const nowIso = new Date().toISOString()
      reminders = await listReminders({ dueBefore: nowIso, completed: false })
    } catch {
      // empty follow-ups
    }
  }

  if (errorMessage || !summary) {
    return (
      <ErrorState
        title="Couldn't load dashboard"
        description={errorMessage ?? "Unable to load your dashboard right now."}
      />
    )
  }

  const followUpsDue = reminders.length
  const recentApplications = applications.slice(0, 5)

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">{greeting()}</h1>
        <p className="text-sm text-muted-foreground">Here&apos;s how your job search is going.</p>
      </header>

      {/* Headline metrics */}
      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Metric
          label="Applications"
          value={summary.totals.applications}
          sub={`${summary.totals.active} active`}
        />
        <Metric
          label="Interviews"
          value={summary.totals.interviews}
          sub="stage reached"
          tone="info"
        />
        <Metric label="Offers" value={summary.totals.offers} tone="good" />
        <Metric
          label="Response rate"
          value={`${summary.response_rate.toFixed(0)}%`}
          sub="of applications"
          tone="accent"
        />
      </section>

      {followUpsDue > 0 && (
        <Link
          href="/reminders"
          className="flex items-center justify-between gap-3 rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 transition-colors hover:bg-amber-500/10"
        >
          <div className="flex items-center gap-2.5">
            <Bell className="size-4 text-amber-600 dark:text-amber-400" />
            <span className="text-sm font-medium">
              {followUpsDue} follow-up{followUpsDue === 1 ? "" : "s"} due
            </span>
          </div>
          <ArrowRight className="size-4 text-muted-foreground" />
        </Link>
      )}

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.6fr_1fr]">
        {/* Recent activity */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="size-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                Recent activity
              </h2>
            </div>
            <Button asChild variant="ghost" size="sm">
              <Link href="/applications">
                View all
                <ArrowRight className="ml-1 h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
          {recentApplications.length === 0 ? (
            <div className="rounded-lg border border-dashed p-8 text-center">
              <ClipboardList className="mx-auto mb-2 size-6 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                No applications yet. Add your first role to start the pipeline.
              </p>
            </div>
          ) : (
            <ul className="divide-y rounded-lg border">
              {recentApplications.map((app) => (
                <li key={app.id}>
                  <Link
                    href={`/applications/${app.id}`}
                    className="flex items-center justify-between gap-3 px-4 py-3 transition-colors hover:bg-muted/40"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{app.role_title}</p>
                      <p className="truncate text-xs text-muted-foreground">
                        {app.company?.name ?? "Unknown"}
                        {app.stage && ` · ${app.stage.name}`}
                      </p>
                    </div>
                    <ApplicationStatusBadge status={app.status} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Sidebar: quick links */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <TrendingUp className="size-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              Jump back in
            </h2>
          </div>
          <div className="grid gap-2">
            <QuickLink href="/pipeline" label="Pipeline" description="Drag-and-drop Kanban" />
            <QuickLink href="/analytics" label="Analytics" description="Funnel and trends" />
            <QuickLink href="/interviews" label="Interviews" description="Scheduled and past" />
            <QuickLink href="/reminders" label="Reminders" description="Follow-ups and due dates" />
          </div>
          {followUpsDue > 0 && (
            <div className="rounded-md border border-border bg-muted/30 p-3">
              <p className="text-xs text-muted-foreground">Up next</p>
              <ul className="mt-2 space-y-1.5">
                {reminders.slice(0, 3).map((r) => (
                  <li key={r.id} className="flex items-center justify-between gap-2 text-sm">
                    <span className="truncate">{r.title}</span>
                    <Badge variant="outline" className="shrink-0">
                      {formatDate(r.due_at)}
                    </Badge>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Metric({
  label,
  value,
  sub,
  tone = "default",
}: {
  label: string
  value: number | string
  sub?: string
  tone?: "default" | "good" | "info" | "accent"
}) {
  const valueClass = {
    default: "text-foreground",
    good: "text-emerald-600 dark:text-emerald-400",
    info: "text-blue-600 dark:text-blue-400",
    accent: "text-primary",
  }[tone]
  return (
    <div className="rounded-lg border bg-card p-4">
      <p className={`text-2xl font-semibold tabular-nums ${valueClass}`}>{value}</p>
      <p className="mt-0.5 text-xs text-muted-foreground">{label}</p>
      {sub && <p className="mt-0.5 text-[11px] text-muted-foreground/80">{sub}</p>}
    </div>
  )
}

function QuickLink({
  href,
  label,
  description,
}: {
  href: string
  label: string
  description: string
}) {
  return (
    <Link
      href={href}
      className="flex items-center justify-between gap-2 rounded-md border px-3 py-2.5 transition-colors hover:bg-muted/40"
    >
      <div>
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      <ArrowRight className="size-4 text-muted-foreground" />
    </Link>
  )
}

function greeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return "Good morning"
  if (hour < 18) return "Good afternoon"
  return "Good evening"
}

function formatDate(value: string | null): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" })
}
