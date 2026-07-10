import { AlertCircle } from "lucide-react"

import { listApplications, listCompanies } from "@/lib/api-client"
import type { Application, Company } from "@/lib/types"
import { ApplicationsTable } from "@/features/applications/applications-table"

export const dynamic = "force-dynamic"

export default async function ApplicationsPage() {
  // Fetch both resources; a companies failure is non-fatal (the application
  // form simply shows an empty company list), but an applications failure
  // surfaces an error state.
  let applications: Application[] = []
  let companies: Company[] = []
  let errorMessage: string | null = null

  try {
    applications = await listApplications()
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : "Unable to load applications right now."
  }

  try {
    companies = await listCompanies()
  } catch {
    // Non-fatal: the table still renders; the create/edit form will show an
    // empty company list and prompt the user to add one.
  }

  if (errorMessage) {
    return (
      <div className="mx-auto mt-12 w-full max-w-md rounded-lg border border-border bg-card p-6 text-card-foreground shadow-sm">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <h2 className="text-lg font-semibold">Couldn&apos;t load applications</h2>
        </div>
        <p className="mt-2 text-sm text-muted-foreground">{errorMessage}</p>
      </div>
    )
  }

  return <ApplicationsTable applications={applications} companies={companies} />
}
