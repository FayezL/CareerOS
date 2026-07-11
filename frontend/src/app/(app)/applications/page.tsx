import type { Metadata } from "next"

import { listApplications, listCompanies } from "@/services/api-client"
import type { Application, Company } from "@/types"
import { ErrorState } from "@/components/error-state"
import { ApplicationsTable } from "@/features/applications/applications-table"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Applications",
}

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
    return <ErrorState title="Couldn't load applications" description={errorMessage} />
  }

  return <ApplicationsTable applications={applications} companies={companies} />
}
