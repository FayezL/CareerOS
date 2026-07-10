import type { Metadata } from "next"
import { AlertCircle } from "lucide-react"

import { listApplications, listCompanies, listStages } from "@/lib/api-client"
import type { Application, Company, PipelineStage } from "@/lib/types"
import { KanbanBoard } from "@/features/pipeline/kanban-board"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Pipeline · CareerOS",
}

export default async function PipelinePage() {
  let stages: PipelineStage[] = []
  let applications: Application[] = []
  let companies: Company[] = []
  let errorMessage: string | null = null

  try {
    stages = await listStages()
  } catch (error) {
    errorMessage =
      error instanceof Error ? error.message : "Unable to load your pipeline right now."
  }

  // Applications and companies are non-fatal: the board still renders its
  // columns when either fails (it simply shows an empty / unknown state).
  try {
    applications = await listApplications()
  } catch {
    // surfaced by the empty/unknown handling in the board
  }

  try {
    companies = await listCompanies()
  } catch {
    // non-fatal: cards fall back to "Unknown" company names
  }

  if (errorMessage) {
    return (
      <div className="mx-auto mt-12 w-full max-w-md rounded-lg border border-border bg-card p-6 text-card-foreground shadow-sm">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <h2 className="text-lg font-semibold">Couldn&apos;t load your pipeline</h2>
        </div>
        <p className="mt-2 text-sm text-muted-foreground">{errorMessage}</p>
      </div>
    )
  }

  return <KanbanBoard stages={stages} applications={applications} companies={companies} />
}
