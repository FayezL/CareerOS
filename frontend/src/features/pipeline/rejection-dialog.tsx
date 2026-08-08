"use client"

import { useState } from "react"
import { toast } from "sonner"

import type { RejectionReasonCategory } from "@/types"
import { REJECTION_CATEGORY_OPTIONS } from "@/features/applications/rejection-categories"
import { moveApplication } from "./actions"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"

type RejectionDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  applicationId: string
  toStageId: string
  onSuccess?: () => void
}

export function RejectionDialog({
  open,
  onOpenChange,
  applicationId,
  toStageId,
  onSuccess,
}: RejectionDialogProps) {
  const [category, setCategory] = useState<RejectionReasonCategory | "">("")
  const [reason, setReason] = useState("")
  const [isPending, setIsPending] = useState(false)

  async function handleConfirm() {
    setIsPending(true)
    const result = await moveApplication(applicationId, toStageId, {
      rejection_reason_category: category || undefined,
      rejection_reason: reason.trim() || undefined,
    })
    setIsPending(false)

    if (result.ok) {
      toast.success("Moved to Rejected")
      onOpenChange(false)
      onSuccess?.()
    } else {
      toast.error(result.error ?? "Failed to move application")
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Move to Rejected</AlertDialogTitle>
          <AlertDialogDescription>
            Optionally capture why this application was rejected. You can change this later.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label htmlFor="rejection-category">Reason category</Label>
            <Select
              value={category}
              onValueChange={(v) => setCategory(v as RejectionReasonCategory)}
            >
              <SelectTrigger id="rejection-category" className="w-full">
                <SelectValue placeholder="Select a reason (optional)" />
              </SelectTrigger>
              <SelectContent>
                {REJECTION_CATEGORY_OPTIONS.map((c) => (
                  <SelectItem key={c.value} value={c.value}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="rejection-text">Details (optional)</Label>
            <Textarea
              id="rejection-text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Salary was 30% below market"
              rows={3}
              maxLength={255}
            />
          </div>
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            disabled={isPending}
            onClick={(e) => {
              e.preventDefault()
              handleConfirm()
            }}
          >
            {isPending ? "Moving…" : "Move to Rejected"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
