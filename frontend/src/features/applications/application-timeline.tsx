import { ArrowRight, FileText, Send } from "lucide-react"

import type { Application, StageHistory } from "@/types"
import { cn } from "@/utils/cn"

type ApplicationTimelineProps = {
  application: Application
  history: StageHistory[]
}

type TimelineEntry = {
  id: string
  icon: typeof Send
  title: string
  subtitle: string | null
  note: string | null
  at: string
  tone: "primary" | "muted"
}

/**
 * Vertical timeline for an application workspace.
 *
 * Combines a synthetic "Applied" entry (derived from the application's
 * applied_at / created_at) with the auditable stage-transition history, telling
 * the full story at a glance: Applied → screen → technical → offer, etc.
 * Chronological (oldest first) so it reads as a narrative.
 */
export function ApplicationTimeline({ application, history }: ApplicationTimelineProps) {
  const entries = buildEntries(application, history)

  if (entries.length === 0) {
    return (
      <p className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
        No activity yet.
      </p>
    )
  }

  return (
    <ol className="relative space-y-1">
      {/* vertical spine */}
      <span
        aria-hidden
        className="pointer-events-none absolute bottom-3 left-[15px] top-3 w-px bg-border"
      />
      {entries.map((entry, i) => {
        const isLast = i === entries.length - 1
        return (
          <li key={entry.id} className="relative flex gap-4 pb-6 last:pb-0">
            <span
              aria-hidden
              className={cn(
                "z-10 mt-1 flex size-8 shrink-0 items-center justify-center rounded-full border",
                entry.tone === "primary"
                  ? "border-primary/30 bg-primary/10 text-primary"
                  : "border-border bg-background text-muted-foreground",
              )}
            >
              <entry.icon className="size-4" />
            </span>
            <div className="min-w-0 flex-1 pt-0.5">
              <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                <p className="text-sm font-medium text-foreground">{entry.title}</p>
                <time className="font-mono text-xs text-muted-foreground">{entry.at}</time>
              </div>
              {entry.subtitle && (
                <p className="mt-0.5 text-sm text-muted-foreground">{entry.subtitle}</p>
              )}
              {entry.note && (
                <p className="mt-2 rounded-md border border-border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
                  {entry.note}
                </p>
              )}
              {isLast && entries.length > 1 && (
                <p className="mt-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Current
                </p>
              )}
            </div>
          </li>
        )
      })}
    </ol>
  )
}

function buildEntries(application: Application, history: StageHistory[]): TimelineEntry[] {
  const entries: TimelineEntry[] = []

  // Synthetic "Applied" entry — always first.
  const appliedDate = application.applied_at ?? application.created_at
  entries.push({
    id: "applied",
    icon: Send,
    title: `Applied to ${application.company?.name ?? "company"}`,
    subtitle: application.role_title,
    note: null,
    at: formatDate(appliedDate),
    tone: "primary",
  })

  // Stage transitions, chronological (backend already returns oldest-first).
  for (const h of history) {
    const fromName = h.from_stage?.name
    const toName = h.to_stage.name
    entries.push({
      id: h.id,
      icon: ArrowRight,
      title: fromName ? `Moved from ${fromName} to ${toName}` : `Moved to ${toName}`,
      subtitle: null,
      note: h.note,
      at: formatTimestamp(h.changed_at),
      tone: "muted",
    })
  }

  // Terminal status marker if the application is closed out.
  if (application.status === "accepted") {
    entries.push({
      id: "accepted",
      icon: FileText,
      title: "Accepted offer",
      subtitle: null,
      note: null,
      at: "",
      tone: "primary",
    })
  } else if (application.status === "rejected") {
    entries.push({
      id: "rejected",
      icon: FileText,
      title: "Rejected",
      subtitle: null,
      note: null,
      at: "",
      tone: "muted",
    })
  }

  return entries
}

function formatDate(value: string | null): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })
}

function formatTimestamp(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}
