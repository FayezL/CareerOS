"use client"

import { useEffect, useState, useTransition } from "react"
import { XCircle } from "lucide-react"
import { toast } from "sonner"

import type { Application, RejectionReasonCategory } from "@/types"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { REJECTION_CATEGORY_OPTIONS, REJECTION_CATEGORY_LABELS } from "./rejection-categories"
import { updateRejectionDetails } from "./actions"

type RejectionDetailsProps = {
  application: Application
}

// Sentinel value for the "no category" option in the Select. We can't use the
// empty string (Select requires non-empty values), so we use a stable token.
const NO_CATEGORY = "__none__"

/**
 * Sidebar panel for editing an application's rejection reason. Visible whenever
 * the application has rejection data OR currently sits in a "Rejected" stage.
 *
 * This is the always-visible editing surface for rejection info (complementing
 * the RejectionDialog shown at move time). Saves go through a dedicated server
 * action that PATCHes only the rejection fields.
 */
export function RejectionDetails({ application }: RejectionDetailsProps) {
  const isRejectedStage = application.stage?.name.trim().toLowerCase() === "rejected"
  const hasRejectionInfo = !!application.rejection_reason_category || !!application.rejection_reason

  const [category, setCategory] = useState<RejectionReasonCategory | typeof NO_CATEGORY>(
    application.rejection_reason_category ?? NO_CATEGORY,
  )
  const [reason, setReason] = useState(application.rejection_reason ?? "")
  const [isPending, startTransition] = useTransition()

  // Re-sync local state if the server-refreshed application changes (e.g. after
  // a route revalidation triggered by another mutation on this page).
  useEffect(() => {
    setCategory(application.rejection_reason_category ?? NO_CATEGORY)
    setReason(application.rejection_reason ?? "")
  }, [application.rejection_reason_category, application.rejection_reason])

  if (!hasRejectionInfo && !isRejectedStage) {
    return null
  }

  function handleSave() {
    const resolvedCategory = category === NO_CATEGORY ? null : (category as RejectionReasonCategory)
    const resolvedReason = reason.trim() ? reason.trim() : null

    startTransition(async () => {
      const result = await updateRejectionDetails(application.id, {
        rejection_reason_category: resolvedCategory,
        rejection_reason: resolvedReason,
      })
      if (result.ok) {
        toast.success("Rejection details saved")
      } else {
        toast.error(result.error ?? "Failed to save rejection details")
      }
    })
  }

  function handleClear() {
    setCategory(NO_CATEGORY)
    setReason("")
    startTransition(async () => {
      const result = await updateRejectionDetails(application.id, {
        rejection_reason_category: null,
        rejection_reason: null,
      })
      if (result.ok) {
        toast.success("Rejection details cleared")
      } else {
        toast.error(result.error ?? "Failed to clear rejection details")
      }
    })
  }

  const categoryValue = application.rejection_reason_category ?? undefined
  const resolvedLabelFor = (c: RejectionReasonCategory) => REJECTION_CATEGORY_LABELS[c]

  return (
    <section className="space-y-3 border-t border-border pt-5">
      <div className="flex items-center gap-2">
        <XCircle className="size-4 text-red-500" />
        <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Rejection
        </h2>
      </div>

      <div className="space-y-3">
        <div className="space-y-2">
          <Label htmlFor="rejection-category" className="text-xs text-muted-foreground">
            Reason category
          </Label>
          <Select
            value={category}
            onValueChange={(v) => setCategory(v as RejectionReasonCategory | typeof NO_CATEGORY)}
          >
            <SelectTrigger id="rejection-category" className="w-full">
              <SelectValue placeholder="Select a reason (optional)" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={NO_CATEGORY}>No category</SelectItem>
              {REJECTION_CATEGORY_OPTIONS.map((c) => (
                <SelectItem key={c.value} value={c.value}>
                  {c.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {categoryValue && (
            <p className="text-xs text-muted-foreground">
              Currently: {resolvedLabelFor(categoryValue)}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="rejection-reason" className="text-xs text-muted-foreground">
            Details
          </Label>
          <Textarea
            id="rejection-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="e.g. Salary was 30% below market"
            rows={3}
            maxLength={255}
          />
          <p className="text-right text-xs text-muted-foreground">{reason.length}/255</p>
        </div>

        <div className="flex items-center gap-2">
          <Button type="button" size="sm" onClick={handleSave} disabled={isPending}>
            {isPending ? "Saving…" : "Save"}
          </Button>
          {hasRejectionInfo && (
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={handleClear}
              disabled={isPending}
            >
              Clear
            </Button>
          )}
        </div>
      </div>
    </section>
  )
}
