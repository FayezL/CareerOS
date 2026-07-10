import type { Metadata } from "next"
import Link from "next/link"
import { CalendarClock, Clock, MapPin } from "lucide-react"

import { listApplications, listInterviews } from "@/lib/api-client"
import type { Application, Interview, InterviewType } from "@/lib/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/empty-state"
import { ErrorState } from "@/components/error-state"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Interviews",
  description: "Upcoming and past interviews tied to your applications.",
}

const TYPE_LABELS: Record<InterviewType, string> = {
  phone_screen: "Phone screen",
  video_call: "Video call",
  onsite: "Onsite",
  take_home: "Take-home",
  technical: "Technical",
  final: "Final",
}

export default async function InterviewsPage() {
  let interviews: Interview[] = []
  let applications: Application[] = []
  let errorMessage: string | null = null

  try {
    interviews = await listInterviews()
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : "Unable to load interviews right now."
  }

  // Non-fatal: enrich rows with the linked application's role and company.
  try {
    applications = await listApplications()
  } catch {
    // Fall back to bare interview rows without application context.
  }

  if (errorMessage) {
    return <ErrorState title="Couldn't load interviews" description={errorMessage} />
  }

  if (interviews.length === 0) {
    return (
      <div className="space-y-6">
        <Header />
        <EmptyState
          icon={CalendarClock}
          title="No interviews yet"
          description="Scheduled interviews from your applications will appear here."
          action={
            <Button asChild variant="outline">
              <Link href="/applications">Browse applications</Link>
            </Button>
          }
        />
      </div>
    )
  }

  const applicationMap = buildApplicationMap(applications)
  const { upcoming, past } = splitByTime(interviews)

  return (
    <div className="space-y-6">
      <Header />

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-muted-foreground">
          Upcoming{" "}
          {upcoming.length > 0 && (
            <span className="text-muted-foreground">({upcoming.length})</span>
          )}
        </h2>
        {upcoming.length === 0 ? (
          <p className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
            Nothing scheduled. You&apos;re all caught up.
          </p>
        ) : (
          <ul className="space-y-2">
            {upcoming.map((interview) => (
              <InterviewRow
                key={interview.id}
                interview={interview}
                application={applicationMap.get(interview.application_id)}
              />
            ))}
          </ul>
        )}
      </section>

      {past.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-muted-foreground">Past</h2>
          <ul className="space-y-2">
            {past.map((interview) => (
              <InterviewRow
                key={interview.id}
                interview={interview}
                application={applicationMap.get(interview.application_id)}
              />
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}

function Header() {
  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Interviews</h1>
      <p className="text-sm text-muted-foreground">
        Upcoming and past interviews, by scheduled time.
      </p>
    </div>
  )
}

function InterviewRow({
  interview,
  application,
}: {
  interview: Interview
  application?: Application
}) {
  return (
    <li className="flex flex-col gap-2 rounded-lg border bg-card p-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary">{TYPE_LABELS[interview.type]}</Badge>
          {application ? (
            <Link
              href={`/applications/${application.id}`}
              className="truncate font-medium hover:underline"
            >
              {application.role_title}
              {application.company ? ` · ${application.company.name}` : ""}
            </Link>
          ) : (
            <span className="truncate font-medium text-muted-foreground">Application removed</span>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatDateTime(interview.scheduled_at)}
          </span>
          {interview.duration_minutes ? <span>{interview.duration_minutes} min</span> : null}
          {interview.location ? (
            <span className="inline-flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              {interview.location}
            </span>
          ) : null}
        </div>
        {interview.notes ? (
          <p className="text-xs text-muted-foreground">{interview.notes}</p>
        ) : null}
      </div>
    </li>
  )
}

function buildApplicationMap(applications: Application[]): Map<string, Application> {
  const map = new Map<string, Application>()
  for (const application of applications) {
    map.set(application.id, application)
  }
  return map
}

function splitByTime(interviews: Interview[]): { upcoming: Interview[]; past: Interview[] } {
  const now = Date.now()
  const upcoming = interviews
    .filter((i) => new Date(i.scheduled_at).getTime() >= now)
    .sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime())
  const past = interviews
    .filter((i) => new Date(i.scheduled_at).getTime() < now)
    .sort((a, b) => new Date(b.scheduled_at).getTime() - new Date(a.scheduled_at).getTime())
  return { upcoming, past }
}

function formatDateTime(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date)
}
