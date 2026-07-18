import { History } from "lucide-react"

import type { StageHistory } from "@/types"

type StageHistoryTimelineProps = {
  history: StageHistory[]
}

/** Renders the auditable stage-transition log for an application. */
export function StageHistoryTimeline({ history }: StageHistoryTimelineProps) {
  if (history.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-8 text-center">
        <History className="h-5 w-5 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">No stage changes recorded yet.</p>
      </div>
    )
  }

  return (
    <ol className="relative space-y-4 border-l border-border pl-6">
      {history.map((entry) => (
        <li key={entry.id} className="relative">
          <span
            aria-hidden
            className="absolute -left-[27px] top-1.5 h-3 w-3 rounded-full border-2 border-background bg-primary"
          />
          <div className="flex flex-wrap items-baseline justify-between gap-x-3">
            <span className="text-sm font-medium">{entry.to_stage.name}</span>
            <time className="font-mono text-xs text-muted-foreground">
              {formatTimestamp(entry.changed_at)}
            </time>
          </div>
          {entry.note ? <p className="mt-1 text-sm text-muted-foreground">{entry.note}</p> : null}
        </li>
      ))}
    </ol>
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
