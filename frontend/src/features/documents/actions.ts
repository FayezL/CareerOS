"use server"

import { revalidatePath } from "next/cache"

import { apiFetch } from "@/services/api-client"
import type { Document, DocumentType } from "@/types"

export type ActionResult = { ok: boolean; error?: string }

/** Input for creating a document's metadata row (matches POST /documents). */
export type CreateDocumentInput = {
  application_id: string
  type: DocumentType
  name: string
  mime_type: string
  size_bytes: number
}

/** Input for creating a revision (matches POST /documents/{id}/revisions). */
export type CreateRevisionInput = {
  rootId: string
  name: string
  mime_type: string
  size_bytes: number
  version_label?: string
}

/** Result of a create; carries the created document (incl. its upload URL). */
export type CreateDocumentResult = {
  ok: boolean
  document?: Document
  error?: string
}

export type CreateRevisionResult = {
  ok: boolean
  document?: Document
  error?: string
}

function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) return error.message
  return "Something went wrong. Please try again."
}

/** The application detail route that owns this panel's documents. */
function applicationDetailPath(applicationId: string): string {
  return `/applications/${applicationId}`
}

/**
 * Create a document's metadata and request a signed upload URL. The returned
 * document carries `upload_url` (and friends); the client uploads the bytes
 * directly to it. Revalidates the owning application detail route.
 */
export async function createDocumentMetadata(
  input: CreateDocumentInput,
): Promise<CreateDocumentResult> {
  try {
    const document = await apiFetch<Document>("/documents", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    })
    revalidatePath(applicationDetailPath(input.application_id))
    return { ok: true, document }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

/**
 * Create a document revision and request a signed upload URL. The returned
 * document carries `upload_url` (and friends); the client uploads the bytes
 * directly to it. Revalidates the documents route.
 */
export async function createDocumentRevision(
  input: CreateRevisionInput,
): Promise<CreateRevisionResult> {
  try {
    const document = await apiFetch<Document>(`/documents/${input.rootId}/revisions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: input.name,
        mime_type: input.mime_type,
        size_bytes: input.size_bytes,
        version_label: input.version_label || undefined,
      }),
    })
    revalidatePath("/documents")
    return { ok: true, document }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

/**
 * Delete a document (metadata + underlying object) and revalidate the owning
 * application detail route.
 */
export async function deleteDocument(id: string, applicationId: string): Promise<ActionResult> {
  try {
    await apiFetch(`/documents/${id}`, { method: "DELETE" })
    revalidatePath(applicationDetailPath(applicationId))
    revalidatePath("/documents")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}
