import type { Metadata } from "next"

import { listApplications, listCompanies, listStages } from "@/lib/api-client"
import type { Application, Company, PipelineStage } from "@/lib/types"
import { ErrorState } from "@/components/error-state"
import { KanbanBoard } from "@/features/pipeline/kanban-board"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Pipeline",
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
    return <ErrorState title="Couldn't load your pipeline" description={errorMessage} />
  }

  return <KanbanBoard stages={stages} applications={applications} companies={companies} />
}
