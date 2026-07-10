"use server"

import { revalidatePath } from "next/cache"

import { apiFetch } from "@/lib/api-client"
import type { Document, DocumentType } from "@/lib/types"

export type ActionResult = { ok: boolean; error?: string }

/** Input for creating a document's metadata row (matches POST /documents). */
export type CreateDocumentInput = {
  application_id: string
  type: DocumentType
  name: string
  mime_type: string
  size_bytes: number
}

/** Result of a create; carries the created document (incl. its upload URL). */
export type CreateDocumentResult = {
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
 * Delete a document (metadata + underlying object) and revalidate the owning
 * application detail route.
 */
export async function deleteDocument(id: string, applicationId: string): Promise<ActionResult> {
  try {
    await apiFetch(`/documents/${id}`, { method: "DELETE" })
    revalidatePath(applicationDetailPath(applicationId))
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}
