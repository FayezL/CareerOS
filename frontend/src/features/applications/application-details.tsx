import { Building2, ExternalLink, FileText, Globe, MapPin, Wallet } from "lucide-react"

import type { Application } from "@/types"
import { Badge } from "@/components/ui/badge"
import { ApplicationStatusBadge } from "./status-badge"

type ApplicationDetailsProps = {
  application: Application
}

/**
 * Sidebar panel for the application workspace — the at-a-glance facts (status,
 * stage, source, salary, dates) plus the company block and the job description.
 * Read-only presentation; edits go through the application form elsewhere.
 */
export function ApplicationDetails({ application }: ApplicationDetailsProps) {
  const salary = formatSalary(
    application.salary_min,
    application.salary_max,
    application.salary_currency,
  )

  return (
    <aside className="space-y-6">
      <section className="space-y-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Status
        </h2>
        <div className="flex flex-wrap items-center gap-2">
          <ApplicationStatusBadge status={application.status} />
          {application.stage && <Badge variant="outline">{application.stage.name}</Badge>}
        </div>
      </section>

      <DetailRow icon={FileText} label="Applied">
        {formatDate(application.applied_at) ?? "Not set"}
      </DetailRow>
      <DetailRow icon={Globe} label="Source">
        {application.source ?? "—"}
      </DetailRow>
      {salary && (
        <DetailRow icon={Wallet} label="Salary">
          {salary}
        </DetailRow>
      )}

      {application.company && (
        <section className="space-y-3 border-t border-border pt-5">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Company
          </h2>
          <div className="flex items-start gap-2.5">
            <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground">
              <Building2 className="size-4" />
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{application.company.name}</p>
              <CompanyMeta application={application} />
            </div>
          </div>
        </section>
      )}

      {application.job_description && (
        <section className="space-y-2 border-t border-border pt-5">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Job description
          </h2>
          <p className="whitespace-pre-line text-sm leading-relaxed text-muted-foreground line-clamp-[20]">
            {application.job_description}
          </p>
        </section>
      )}
    </aside>
  )
}

function DetailRow({
  icon: Icon,
  label,
  children,
}: {
  icon: typeof MapPin
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex items-center gap-2.5 text-sm">
      <Icon className="size-4 shrink-0 text-muted-foreground" />
      <span className="w-20 shrink-0 text-muted-foreground">{label}</span>
      <span className="min-w-0 truncate font-medium">{children}</span>
    </div>
  )
}

function CompanyMeta({ application }: { application: Application }) {
  // The embedded company ref only carries id+name; show the job url as the
  // external link when present. Richer company metadata lands in Phase 3.
  if (!application.job_url) return null
  return (
    <a
      href={application.job_url}
      target="_blank"
      rel="noopener noreferrer"
      className="mt-0.5 inline-flex items-center gap-1 text-xs text-primary hover:underline"
    >
      View job posting
      <ExternalLink className="size-3" />
    </a>
  )
}

function formatDate(value: string | null): string | null {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })
}

function formatSalary(
  min: number | null,
  max: number | null,
  currency: string | null,
): string | null {
  if (min == null && max == null) return null
  const cur = currency ?? ""
  const fmt = (n: number) => `${cur}${n.toLocaleString()}`
  if (min != null && max != null) return `${fmt(min)} – ${fmt(max)}`
  return fmt(min ?? max!)
}
