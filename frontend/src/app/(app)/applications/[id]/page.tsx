import type { Metadata } from "next"
import Link from "next/link"
import { ArrowLeft, ExternalLink, History, Pencil } from "lucide-react"

import {
  getApplication,
  listDocuments,
  listStageHistory,
  listInterviews,
  listNotes,
  listTimelineEvents,
} from "@/services/api-client"
import type { Application, Document, StageHistory, Interview, Note, TimelineEvent } from "@/types"
import { Button } from "@/components/ui/button"
import { ErrorState } from "@/components/error-state"
import { ApplicationForm } from "@/features/applications/application-form"
import { ApplicationTimeline } from "@/features/applications/application-timeline"
import { ApplicationDetails } from "@/features/applications/application-details"
import { RejectionDetails } from "@/features/applications/rejection-details"
import { ApplicationStatusBadge } from "@/features/applications/status-badge"
import { TagBadges } from "@/features/applications/tag-badges"
import { DocumentsPanel } from "@/features/documents/documents-panel"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Application",
  description: "Application workspace — timeline, details, and documents.",
}

type PageProps = {
  params: Promise<{ id: string }>
}

export default async function ApplicationDetailPage({ params }: PageProps) {
  const { id } = await params

  let application: Application | null = null
  let documents: Document[] = []
  let history: StageHistory[] = []
  let interviews: Interview[] = []
  let notes: Note[] = []
  let timelineEvents: TimelineEvent[] = []
  let errorMessage: string | null = null

  try {
    application = await getApplication(id)
  } catch (error) {
    errorMessage =
      error instanceof Error ? error.message : "Unable to load this application right now."
  }

  if (application) {
    try {
      history = await listStageHistory(id)
    } catch {
      // empty timeline is fine
    }
    try {
      interviews = await listInterviews()
    } catch {
      // empty interviews is fine
    }
    try {
      notes = await listNotes(id)
    } catch {
      // empty notes is fine
    }
    try {
      timelineEvents = await listTimelineEvents(id)
    } catch {
      // empty timeline events is fine
    }
    try {
      const result = await listDocuments({ applicationId: id })
      documents = result?.items ?? []
    } catch {
      // empty documents panel is fine
    }
  }

  if (errorMessage || !application) {
    return (
      <ErrorState
        title="Couldn't load application"
        description={errorMessage ?? "Unable to load this application right now."}
      />
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between gap-4">
        <Button asChild variant="ghost" size="sm" className="-ml-2">
          <Link href="/applications">
            <ArrowLeft className="h-4 w-4" />
            Applications
          </Link>
        </Button>
        <ApplicationForm
          application={application}
          trigger={
            <Button variant="outline" size="sm">
              <Pencil className="mr-2 h-4 w-4" />
              Edit
            </Button>
          }
        />
      </div>

      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">{application.role_title}</h1>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
          {application.company ? (
            <Link
              href={`/companies/${application.company.id}`}
              className="font-medium text-foreground hover:underline"
            >
              {application.company.name}
            </Link>
          ) : (
            <span>Unknown company</span>
          )}
          {application.stage && (
            <>
              <span aria-hidden>·</span>
              <span>{application.stage.name}</span>
            </>
          )}
          <span aria-hidden>·</span>
          <ApplicationStatusBadge status={application.status} />
          {application.applied_at && (
            <>
              <span aria-hidden>·</span>
              <span>Applied {formatDate(application.applied_at)}</span>
            </>
          )}
        </div>
        {application.job_url && (
          <a
            href={application.job_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
          >
            View job posting
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        )}
        {application.tags.length > 0 && <TagBadges tags={application.tags} className="pt-1" />}
      </header>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.6fr_1fr]">
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <History className="size-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              Timeline
            </h2>
          </div>
          <ApplicationTimeline
            application={application}
            history={history}
            interviews={interviews.filter((i) => i.application_id === id)}
            notes={notes}
            timelineEvents={timelineEvents}
            onRefresh={async () => {
              // This is a client-side trigger - the page will reload on the next navigation
            }}
          />
        </section>

        <div className="space-y-8">
          <ApplicationDetails application={application} />
          <RejectionDetails application={application} />
          <div className="border-t border-border pt-6">
            <DocumentsPanel applicationId={application.id} initial={documents} />
          </div>
        </div>
      </div>
    </div>
  )
}

function formatDate(value: string | null): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })
}
