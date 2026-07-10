import type { ApplicationStatus } from "@/lib/types"
import { Badge } from "@/components/ui/badge"

type StatusBadgeProps = {
  status: ApplicationStatus
}

/** Application status badge — pairs a colored tint with a text label. */
export function StatusBadge({ status }: StatusBadgeProps) {
  switch (status) {
    case "active":
      return <Badge>Active</Badge>
    case "accepted":
      return (
        <Badge className="border-green-500/30 bg-green-500/10 text-green-700 dark:border-green-400/30 dark:text-green-400">
          Accepted
        </Badge>
      )
    case "rejected":
      return <Badge variant="destructive">Rejected</Badge>
    case "archived":
      return <Badge variant="outline">Archived</Badge>
  }
}
