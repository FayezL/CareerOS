import type { Metadata } from "next"

import { listDocuments } from "@/services/api-client"
import type { DocumentType } from "@/types"
import { ErrorState } from "@/components/error-state"
import { DocumentManager } from "@/features/documents/document-manager"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Documents",
  description: "Document Manager — resumes, cover letters, and supporting files.",
}

type PageProps = {
  searchParams: Promise<{ type?: string }>
}

export default async function DocumentsPage({ searchParams }: PageProps) {
  const { type } = await searchParams
  const activeType = isDocumentType(type) ? type : undefined

  try {
    const page = await listDocuments(activeType ? { type: activeType } : undefined)
    return (
      <DocumentManager
        initial={page.items}
        nextCursor={page.next_cursor ?? null}
        initialType={activeType}
      />
    )
  } catch (error) {
    return (
      <ErrorState
        title="Couldn't load documents"
        description={error instanceof Error ? error.message : "Please try again."}
      />
    )
  }
}

function isDocumentType(value: string | undefined): value is DocumentType {
  return (
    !!value &&
    ["resume", "cover_letter", "certificate", "reference", "visa", "other"].includes(value)
  )
}
