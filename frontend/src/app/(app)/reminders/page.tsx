import type { Metadata } from "next"
import { Bell, Plus } from "lucide-react"

import { listApplications, listInterviews, listReminders } from "@/lib/api-client"
import type { Application, Interview, Reminder } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/empty-state"
import { ErrorState } from "@/components/error-state"
import { ReminderForm } from "@/features/reminders/reminder-form"
import { RemindersList } from "@/features/reminders/reminders-list"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Reminders",
  description: "Follow-ups and interview prep nudges, grouped by what's due.",
}

export default async function RemindersPage() {
  let reminders: Reminder[] = []
  let errorMessage: string | null = null

  try {
    reminders = await listReminders({ limit: 100 })
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : "Unable to load reminders right now."
  }

  // Non-fatal: the create form still renders with title + due date only.
  let applications: Application[] = []
  let interviews: Interview[] = []
  try {
    applications = await listApplications()
  } catch {
    // ignore — form hides the application select when absent
  }
  try {
    interviews = await listInterviews()
  } catch {
    // ignore — form hides the interview select when absent
  }

  if (errorMessage) {
    return <ErrorState title="Couldn't load reminders" description={errorMessage} />
  }

  if (reminders.length === 0) {
    return (
      <div className="space-y-6">
        <Header />
        <EmptyState
          icon={Bell}
          title="No reminders yet"
          description="Add a follow-up so nothing slips through the cracks."
          action={
            <ReminderForm
              applications={applications}
              interviews={interviews}
              trigger={
                <Button variant="outline">
                  <Plus className="mr-2 h-4 w-4" />
                  New reminder
                </Button>
              }
            />
          }
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <Header />
        <ReminderForm
          applications={applications}
          interviews={interviews}
          trigger={
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New reminder
            </Button>
          }
        />
      </div>

      <RemindersList reminders={reminders} />
    </div>
  )
}

function Header() {
  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Reminders</h1>
      <p className="text-sm text-muted-foreground">Follow-ups and prep nudges, by due date.</p>
    </div>
  )
}
