import { AlertCircle } from "lucide-react"

import { listCompanies } from "@/lib/api-client"
import type { Company } from "@/lib/types"
import { CompaniesTable } from "@/features/companies/companies-table"

export const dynamic = "force-dynamic"

export default async function CompaniesPage() {
  let companies: Company[] = []
  let errorMessage: string | null = null

  try {
    companies = await listCompanies()
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : "Unable to load companies right now."
  }

  if (errorMessage) {
    return (
      <div className="mx-auto mt-12 w-full max-w-md rounded-lg border border-border bg-card p-6 text-card-foreground shadow-sm">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <h2 className="text-lg font-semibold">Couldn&apos;t load companies</h2>
        </div>
        <p className="mt-2 text-sm text-muted-foreground">{errorMessage}</p>
      </div>
    )
  }

  return <CompaniesTable companies={companies} />
}
