import type { ApplicationStatus } from "@/types"
import { Badge } from "@/components/ui/badge"

const LABELS: Record<ApplicationStatus, string> = {
  active: "Active",
  archived: "Archived",
  rejected: "Rejected",
  accepted: "Accepted",
}

const TONES: Record<ApplicationStatus, string> = {
  active: "border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  archived: "border-border bg-muted text-muted-foreground",
  rejected: "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400",
  accepted: "border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
}

export function ApplicationStatusBadge({ status }: { status: ApplicationStatus }) {
  return (
    <Badge variant="outline" className={TONES[status]}>
      {LABELS[status]}
    </Badge>
  )
}
