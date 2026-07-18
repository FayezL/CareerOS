import type { Metadata } from "next"
import Link from "next/link"
import { ArrowLeft, Briefcase, ExternalLink, Linkedin, MapPin, Users } from "lucide-react"

import { getCompany, listApplications, listContacts } from "@/services/api-client"
import type { Application, Company, Contact } from "@/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ErrorState } from "@/components/error-state"
import { ApplicationStatusBadge } from "@/features/applications/status-badge"
import { CompanyForm } from "@/features/companies/company-form"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Company",
  description: "Your history with this company.",
}

type PageProps = {
  params: Promise<{ id: string }>
}

export default async function CompanyDetailPage({ params }: PageProps) {
  const { id } = await params

  let company: Company | null = null
  let applications: Application[] = []
  let contacts: Contact[] = []
  let errorMessage: string | null = null

  try {
    company = await getCompany(id)
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : "Unable to load this company right now."
  }

  if (company) {
    // Applications + contacts are non-fatal; the dashboard still renders.
    try {
      applications = await listApplications({ companyId: id })
    } catch {
      // empty applications section
    }
    try {
      contacts = await listContacts({ companyId: id })
    } catch {
      // empty contacts section
    }
  }

  if (errorMessage || !company) {
    return (
      <ErrorState
        title="Couldn't load company"
        description={errorMessage ?? "Unable to load this company right now."}
      />
    )
  }

  const stats = computeStats(applications)

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between gap-4">
        <Button asChild variant="ghost" size="sm" className="-ml-2">
          <Link href="/companies">
            <ArrowLeft className="h-4 w-4" />
            Companies
          </Link>
        </Button>
        <CompanyForm
          company={company}
          trigger={
            <Button variant="outline" size="sm">
              Edit
            </Button>
          }
        />
      </div>

      <header className="space-y-3">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex size-11 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Briefcase className="size-5" />
          </span>
          <div className="min-w-0 flex-1">
            <h1 className="text-2xl font-semibold tracking-tight">{company.name}</h1>
            <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
              {company.industry && <span>{company.industry}</span>}
              {company.size && (
                <>
                  <span aria-hidden>·</span>
                  <span>{company.size}</span>
                </>
              )}
              {company.location && (
                <>
                  <span aria-hidden>·</span>
                  <span className="inline-flex items-center gap-1">
                    <MapPin className="size-3.5" />
                    {company.location}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
        {(company.website || company.linkedin_url) && (
          <div className="flex flex-wrap gap-2">
            {company.website && (
              <Button asChild variant="outline" size="sm">
                <a href={company.website} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Website
                </a>
              </Button>
            )}
            {company.linkedin_url && (
              <Button asChild variant="outline" size="sm">
                <a href={company.linkedin_url} target="_blank" rel="noopener noreferrer">
                  <Linkedin className="mr-2 h-4 w-4" />
                  LinkedIn
                </a>
              </Button>
            )}
          </div>
        )}
      </header>

      {/* At-a-glance stats */}
      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Applications" value={stats.total} tone="default" />
        <StatCard label="Active" value={stats.active} tone="active" />
        <StatCard label="Offers" value={stats.offers} tone="good" />
        <StatCard label="Rejected" value={stats.rejected} tone="bad" />
      </section>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.6fr_1fr]">
        {/* Applications at this company */}
        <section className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
            Applications
          </h2>
          {applications.length === 0 ? (
            <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
              No applications at {company.name} yet.
            </div>
          ) : (
            <ul className="divide-y rounded-lg border">
              {applications.map((app) => (
                <li key={app.id}>
                  <Link
                    href={`/applications/${app.id}`}
                    className="flex items-center justify-between gap-3 px-4 py-3 transition-colors hover:bg-muted/40"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{app.role_title}</p>
                      <p className="text-xs text-muted-foreground">
                        {app.stage?.name ?? "No stage"}
                        {app.applied_at && ` · Applied ${formatDate(app.applied_at)}`}
                      </p>
                    </div>
                    <ApplicationStatusBadge status={app.status} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Sidebar: contacts + notes */}
        <div className="space-y-8">
          <section className="space-y-3">
            <div className="flex items-center gap-2">
              <Users className="size-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                Contacts
              </h2>
              {contacts.length > 0 && <Badge variant="outline">{contacts.length}</Badge>}
            </div>
            {contacts.length === 0 ? (
              <p className="text-sm text-muted-foreground">No contacts recorded yet.</p>
            ) : (
              <ul className="space-y-2">
                {contacts.map((c) => (
                  <li key={c.id} className="rounded-md border px-3 py-2">
                    <p className="text-sm font-medium">{c.name}</p>
                    {c.role && <p className="text-xs text-muted-foreground">{c.role}</p>}
                    {c.email && (
                      <a
                        href={`mailto:${c.email}`}
                        className="mt-0.5 block truncate text-xs text-primary hover:underline"
                      >
                        {c.email}
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>

          {company.notes && (
            <section className="space-y-2 border-t border-border pt-5">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                Notes
              </h2>
              <p className="whitespace-pre-line text-sm leading-relaxed text-muted-foreground">
                {company.notes}
              </p>
            </section>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({
  label,
  value,
  tone,
}: {
  label: string
  value: number
  tone: "default" | "active" | "good" | "bad"
}) {
  const toneClass = {
    default: "text-foreground",
    active: "text-blue-600 dark:text-blue-400",
    good: "text-emerald-600 dark:text-emerald-400",
    bad: "text-red-600 dark:text-red-400",
  }[tone]
  return (
    <div className="rounded-lg border bg-card p-4">
      <p className={`text-2xl font-semibold tabular-nums ${toneClass}`}>{value}</p>
      <p className="mt-0.5 text-xs text-muted-foreground">{label}</p>
    </div>
  )
}

function computeStats(applications: Application[]): {
  total: number
  active: number
  offers: number
  rejected: number
} {
  return {
    total: applications.length,
    active: applications.filter((a) => a.status === "active").length,
    offers: applications.filter((a) => a.status === "accepted").length,
    rejected: applications.filter((a) => a.status === "rejected").length,
  }
}

function formatDate(value: string | null): string {
  if (!value) return ""
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })
}
