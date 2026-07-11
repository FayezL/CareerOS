import type { Metadata } from "next"

import { listCompanies } from "@/services/api-client"
import type { Company } from "@/types"
import { ErrorState } from "@/components/error-state"
import { CompaniesTable } from "@/features/companies/companies-table"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Companies",
}

export default async function CompaniesPage() {
  let companies: Company[] = []
  let errorMessage: string | null = null

  try {
    companies = await listCompanies()
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : "Unable to load companies right now."
  }

  if (errorMessage) {
    return <ErrorState title="Couldn't load companies" description={errorMessage} />
  }

  return <CompaniesTable companies={companies} />
}
