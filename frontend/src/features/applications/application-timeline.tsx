"use client"

import { ArrowRight, FileText, Send } from "lucide-react"

import type { Application, StageHistory, Interview, Note, TimelineEvent } from "@/types"
import { cn } from "@/utils/cn"
import { buildTimeline, type TimelineItem } from "@/features/workspace/lib/timeline"
import { DeleteEventDialog } from "@/features/workspace/components/delete-event-dialog"
import { AddEventForm } from "@/features/workspace/components/add-event-form"

type ApplicationTimelineProps = {
  application: Application
  history: StageHistory[]
  interviews: Interview[]
  notes: Note[]
  timelineEvents: TimelineEvent[]
  onRefresh: () => void
}

/**
 * Vertical timeline for an application workspace.
 *
 * Combines stage history, interviews, notes, and custom timeline events
 * into a single chronological narrative (oldest first).
 */
export function ApplicationTimeline({
  application,
  history,
  interviews,
  notes,
  timelineEvents,
  onRefresh,
}: ApplicationTimelineProps) {
  const timelineItems = buildTimeline(application, history, interviews, notes, timelineEvents)

  if (timelineItems.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-12 text-center">
        <p className="text-sm text-muted-foreground">No activity yet.</p>
        <AddEventForm applicationId={application.id} />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Timeline</h3>
        <AddEventForm applicationId={application.id} />
      </div>
      <ol className="relative space-y-1">
        {/* vertical spine */}
        <span
          aria-hidden
          className="pointer-events-none absolute bottom-3 left-[15px] top-3 w-px bg-border"
        />
        {timelineItems.map((item, i) => {
          const Icon = item.metadata.icon
          const isLast = i === timelineItems.length - 1
          return (
            <li key={item.id} className="relative flex gap-4 pb-6 last:pb-0">
              <span
                aria-hidden
                className={cn(
                  "z-10 mt-1 flex size-8 shrink-0 items-center justify-center rounded-full border",
                  item.type === "stage"
                    ? "border-primary/30 bg-primary/10 text-primary"
                    : "border-border bg-background text-muted-foreground",
                )}
              >
                <Icon className="size-4" />
              </span>
              <div className="min-w-0 flex-1 pt-0.5">
                <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                  <p className="text-sm font-medium text-foreground">{item.title}</p>
                  <div className="flex items-center gap-2">
                    <time className="font-mono text-xs text-muted-foreground">
                      {formatTimestamp(item.occurred_at)}
                    </time>
                    {item.type === "custom" && (
                      <DeleteEventDialog eventId={item.id} onSuccess={onRefresh} />
                    )}
                  </div>
                </div>
                {item.metadata.description && (
                  <p className="mt-0.5 text-sm text-muted-foreground">
                    {item.metadata.description}
                  </p>
                )}
                {item.body && (
                  <p className="mt-2 rounded-md border border-border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
                    {item.body}
                  </p>
                )}
                {item.importance && item.importance !== "NORMAL" && (
                  <span
                    className={cn(
                      "mt-1 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                      item.importance === "HIGH"
                        ? "bg-amber-100 text-amber-800"
                        : "bg-red-100 text-red-800",
                    )}
                  >
                    {item.importance}
                  </span>
                )}
                {isLast && timelineItems.length > 1 && (
                  <p className="mt-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Current
                  </p>
                )}
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
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
