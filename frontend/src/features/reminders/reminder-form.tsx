"use client"

import { useActionState, useCallback, useEffect, useState, type ReactNode } from "react"
import { toast } from "sonner"

import type { Application, Interview, Reminder } from "@/lib/types"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import { createReminder, updateReminder, type ActionResult } from "./actions"

type ReminderFormProps = {
  reminder?: Reminder
  trigger: ReactNode
  /** When provided, an optional application can be linked. */
  applications?: Application[]
  /** When provided, an optional interview can be linked. */
  interviews?: Interview[]
}

const NONE = "__none__"

/**
 * Create/edit dialog for a reminder. The outer component owns the dialog's open
 * state and trigger; the inner form (with its `useActionState`) lives inside
 * `DialogContent`, which Radix only mounts while open, so each open starts with
 * a fresh action state and prefilled defaults.
 */
export function ReminderForm({ reminder, trigger, applications, interviews }: ReminderFormProps) {
  const [open, setOpen] = useState(false)
  const close = useCallback(() => setOpen(false), [])

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-[520px]">
        <ReminderFormFields
          reminder={reminder}
          applications={applications}
          interviews={interviews}
          onClose={close}
        />
      </DialogContent>
    </Dialog>
  )
}

type ReminderFormFieldsProps = {
  reminder?: Reminder
  applications?: Application[]
  interviews?: Interview[]
  onClose: () => void
}

function ReminderFormFields({
  reminder,
  applications,
  interviews,
  onClose,
}: ReminderFormFieldsProps) {
  const [state, formAction, isPending] = useActionState<ActionResult, FormData>(
    async (_prevState, formData) => {
      // The `due_at` field is a `datetime-local` input (local wall time); the
      // API expects an ISO 8601 UTC timestamp. Convert before dispatching.
      const dueInput = formData.get("due_at")
      if (typeof dueInput === "string" && dueInput !== "") {
        const iso = new Date(dueInput).toISOString()
        formData.set("due_at", iso)
      }
      // An empty selection should not send a placeholder id to the backend.
      if (formData.get("application_id") === NONE) formData.delete("application_id")
      if (formData.get("interview_id") === NONE) formData.delete("interview_id")

      const fn = reminder ? updateReminder.bind(null, reminder.id) : createReminder
      return fn(formData)
    },
    { ok: false },
  )

  useEffect(() => {
    if (state.ok) {
      toast.success(reminder ? "Reminder updated" : "Reminder created")
      onClose()
    } else if (state.error) {
      toast.error(state.error)
    }
  }, [state, reminder, onClose])

  const defaultApplicationId = reminder?.application_id ?? NONE
  const defaultInterviewId = reminder?.interview_id ?? NONE
  const dueValue = reminder?.due_at ? isoToLocalInput(reminder.due_at) : ""

  return (
    <>
      <DialogHeader>
        <DialogTitle>{reminder ? "Edit reminder" : "New reminder"}</DialogTitle>
        <DialogDescription>
          {reminder ? "Update this reminder." : "Add a follow-up so nothing slips."}
        </DialogDescription>
      </DialogHeader>

      <form action={formAction} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="title">Title</Label>
          <Input
            id="title"
            name="title"
            required
            placeholder="Follow up with recruiter"
            defaultValue={reminder?.title ?? ""}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="due_at">Due</Label>
          <Input id="due_at" name="due_at" type="datetime-local" required defaultValue={dueValue} />
        </div>

        {applications && applications.length > 0 && (
          <div className="space-y-2">
            <Label htmlFor="application_id">Application (optional)</Label>
            <Select name="application_id" defaultValue={defaultApplicationId}>
              <SelectTrigger id="application_id">
                <SelectValue placeholder="None" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NONE}>None</SelectItem>
                {applications.map((app) => (
                  <SelectItem key={app.id} value={app.id}>
                    {app.role_title}
                    {app.company?.name ? ` · ${app.company.name}` : ""}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {interviews && interviews.length > 0 && (
          <div className="space-y-2">
            <Label htmlFor="interview_id">Interview (optional)</Label>
            <Select name="interview_id" defaultValue={defaultInterviewId}>
              <SelectTrigger id="interview_id">
                <SelectValue placeholder="None" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NONE}>None</SelectItem>
                {interviews.map((iv) => (
                  <SelectItem key={iv.id} value={iv.id}>
                    {iv.type} · {iv.scheduled_at.slice(0, 10)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <DialogFooter>
          <Button type="submit" disabled={isPending}>
            {isPending ? "Saving…" : "Save reminder"}
          </Button>
        </DialogFooter>
      </form>
    </>
  )
}

/**
 * Convert an ISO 8601 timestamp into the local `YYYY-MM-DDTHH:mm` value expected
 * by an `<input type="datetime-local">`.
 */
function isoToLocalInput(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ""
  const pad = (n: number) => String(n).padStart(2, "0")
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}`
  )
}
