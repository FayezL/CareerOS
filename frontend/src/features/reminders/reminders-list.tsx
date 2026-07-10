"use client"

import { useMemo, useTransition } from "react"
import { AlarmClock, Check, Clock, Pencil, Trash2 } from "lucide-react"
import { toast } from "sonner"

import type { Reminder } from "@/lib/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

import { ReminderForm } from "./reminder-form"
import { completeReminder, deleteReminder, snoozeReminder } from "./actions"

type RemindersListProps = {
  reminders: Reminder[]
}

export function RemindersList({ reminders }: RemindersListProps) {
  const { open, done } = useMemo(() => groupReminders(reminders), [reminders])

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-muted-foreground">
          To do {open.length > 0 && <span className="text-muted-foreground">({open.length})</span>}
        </h2>
        {open.length === 0 ? (
          <p className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
            Nothing due. You&apos;re all caught up.
          </p>
        ) : (
          <ul className="space-y-2">
            {open.map((reminder) => (
              <ReminderRow key={reminder.id} reminder={reminder} />
            ))}
          </ul>
        )}
      </section>

      {done.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-muted-foreground">Completed</h2>
          <ul className="space-y-2">
            {done.map((reminder) => (
              <ReminderRow key={reminder.id} reminder={reminder} />
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}

function ReminderRow({ reminder }: { reminder: Reminder }) {
  const [isPending, startTransition] = useTransition()
  const overdue = isOverdue(reminder)

  function handleComplete() {
    startTransition(async () => {
      const result = await completeReminder(reminder.id)
      if (result.ok) {
        toast.success("Reminder completed")
      } else {
        toast.error(result.error ?? "Failed to complete reminder")
      }
    })
  }

  function handleSnoozeOneDay() {
    const base = reminder.due_at ? new Date(reminder.due_at) : new Date()
    base.setDate(base.getDate() + 1)
    startTransition(async () => {
      const result = await snoozeReminder(reminder.id, base.toISOString())
      if (result.ok) {
        toast.success("Snoozed by 1 day")
      } else {
        toast.error(result.error ?? "Failed to snooze reminder")
      }
    })
  }

  function handleDelete() {
    startTransition(async () => {
      const result = await deleteReminder(reminder.id)
      if (result.ok) {
        toast.success("Reminder deleted")
      } else {
        toast.error(result.error ?? "Failed to delete reminder")
      }
    })
  }

  return (
    <li className="flex items-center justify-between gap-3 rounded-lg border bg-card p-3">
      <div className="min-w-0 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={
              reminder.completed
                ? "truncate font-medium text-muted-foreground line-through"
                : "truncate font-medium"
            }
          >
            {reminder.title}
          </span>
          {overdue && <Badge variant="destructive">Overdue</Badge>}
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          <span className={overdue ? "font-medium text-destructive" : ""}>
            {formatRelative(reminder.due_at)}
          </span>
          {reminder.due_at && (
            <span className="text-muted-foreground/70">· {formatAbsolute(reminder.due_at)}</span>
          )}
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-1">
        {!reminder.completed && (
          <>
            <Button variant="ghost" size="sm" onClick={handleComplete} disabled={isPending}>
              <Check className="mr-1 h-4 w-4" />
              Complete
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleSnoozeOneDay}
              disabled={isPending}
              title="Snooze 1 day"
            >
              <AlarmClock className="h-4 w-4" />
              <span className="sr-only">Snooze {reminder.title} by 1 day</span>
            </Button>
          </>
        )}
        <ReminderForm
          reminder={reminder}
          trigger={
            <Button variant="ghost" size="icon" disabled={isPending}>
              <Pencil className="h-4 w-4" />
              <span className="sr-only">Edit {reminder.title}</span>
            </Button>
          }
        />
        <Button variant="ghost" size="icon" onClick={handleDelete} disabled={isPending}>
          <Trash2 className="h-4 w-4" />
          <span className="sr-only">Delete {reminder.title}</span>
        </Button>
      </div>
    </li>
  )
}

/** Split reminders into incomplete (open) and completed groups, each sorted. */
function groupReminders(reminders: Reminder[]): { open: Reminder[]; done: Reminder[] } {
  const open = reminders.filter((r) => !r.completed).sort(byDueAscending)
  const done = reminders.filter((r) => r.completed).sort(byDueDescending)
  return { open, done }
}

/** Sort by due date ascending, with undated reminders pushed to the end. */
function byDueAscending(a: Reminder, b: Reminder): number {
  return dueScore(a) - dueScore(b)
}

/** Sort by due date descending (most recent first), undated last. */
function byDueDescending(a: Reminder, b: Reminder): number {
  return dueScore(b) - dueScore(a)
}

/**
 * A sortable timestamp score. Returns `Infinity` for undated reminders so they
 * sink to the bottom regardless of direction.
 */
function dueScore(r: Reminder): number {
  return r.due_at ? new Date(r.due_at).getTime() : Number.POSITIVE_INFINITY
}

/** An incomplete reminder whose due date is in the past. */
function isOverdue(reminder: Reminder): boolean {
  return (
    !reminder.completed && !!reminder.due_at && new Date(reminder.due_at).getTime() < Date.now()
  )
}

/** Human-friendly relative time, e.g. "in 3 days" / "2 days ago". */
function formatRelative(iso: string | null): string {
  if (!iso) return "No due date"
  const target = new Date(iso).getTime()
  if (Number.isNaN(target)) return "No due date"

  const diffMs = target - Date.now()
  const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" })

  const minutes = Math.round(diffMs / 60_000)
  if (Math.abs(minutes) < 60) return rtf.format(minutes, "minute")

  const hours = Math.round(minutes / 60)
  if (Math.abs(hours) < 24) return rtf.format(hours, "hour")

  const days = Math.round(hours / 24)
  if (Math.abs(days) < 30) return rtf.format(days, "day")

  const months = Math.round(days / 30)
  if (Math.abs(months) < 12) return rtf.format(months, "month")

  return rtf.format(Math.round(months / 12), "year")
}

/** A stable absolute date+time string, e.g. "Jul 9, 2026, 4:00 PM". */
function formatAbsolute(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ""
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(d)
}
