import type { Metadata } from "next"
import Link from "next/link"
import { ArrowLeft, ExternalLink } from "lucide-react"

import { getApplication, listDocuments } from "@/services/api-client"
import type { Application, ApplicationStatus, Document } from "@/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ErrorState } from "@/components/error-state"
import { DocumentsPanel } from "@/features/documents/documents-panel"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Application",
  description: "Application details and documents.",
}

type PageProps = {
  params: Promise<{ id: string }>
}

export default async function ApplicationDetailPage({ params }: PageProps) {
  const { id } = await params

  let application: Application | null = null
  let documents: Document[] = []
  let errorMessage: string | null = null

  try {
    application = await getApplication(id)
  } catch (error) {
    errorMessage =
      error instanceof Error ? error.message : "Unable to load this application right now."
  }

  try {
    documents = await listDocuments(id)
  } catch {
    // Non-fatal: the panel still permits uploads; it just starts empty.
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
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2 w-fit">
        <Link href="/applications">
          <ArrowLeft className="h-4 w-4" />
          Applications
        </Link>
      </Button>

      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">{application.role_title}</h1>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
          <span>{application.company?.name ?? "Unknown company"}</span>
          {application.stage ? (
            <>
              <span aria-hidden>·</span>
              <span>{application.stage.name}</span>
            </>
          ) : null}
          <span aria-hidden>·</span>
          <ApplicationStatusBadge status={application.status} />
          <span aria-hidden>·</span>
          <span>Applied {formatDate(application.applied_at)}</span>
        </div>
        {application.job_url ? (
          <a
            href={application.job_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
          >
            View job posting
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        ) : null}
      </header>

      <DocumentsPanel applicationId={application.id} initial={documents} />
    </div>
  )
}

function ApplicationStatusBadge({ status }: { status: ApplicationStatus }) {
  const label = status.charAt(0).toUpperCase() + status.slice(1)
  return <Badge variant="outline">{label}</Badge>
}

function formatDate(value: string | null): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })
}
