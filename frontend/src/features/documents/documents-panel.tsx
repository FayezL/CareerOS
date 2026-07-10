"use client"

import { useRef, useState, type ChangeEvent } from "react"
import { useAuth } from "@clerk/nextjs"
import { FileText, Loader2, Trash2, Upload } from "lucide-react"
import { toast } from "sonner"

import type { Document, DocumentType } from "@/lib/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

import { createDocumentMetadata, deleteDocument } from "./actions"

type DocumentsPanelProps = {
  applicationId: string
  initial: Document[]
}

const DOCUMENT_TYPE_OPTIONS: { value: DocumentType; label: string }[] = [
  { value: "resume", label: "Resume" },
  { value: "cover_letter", label: "Cover letter" },
  { value: "offer_letter", label: "Offer letter" },
  { value: "other", label: "Other" },
]

/**
 * Lists an application's documents and uploads new ones. Creating the metadata
 * happens via a server action; the file bytes are POSTed directly to the
 * backend-returned `upload_url` (local mode multipart upload).
 */
export function DocumentsPanel({ applicationId, initial }: DocumentsPanelProps) {
  const { getToken } = useAuth()
  const [documents, setDocuments] = useState<Document[]>(initial)
  const [selectedType, setSelectedType] = useState<DocumentType>("resume")
  const [uploading, setUploading] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  async function handleFileSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    // Reset so picking the same file again re-triggers `onChange`.
    event.target.value = ""
    if (!file) return

    setUploading(true)
    let createdId: string | null = null
    try {
      const result = await createDocumentMetadata({
        application_id: applicationId,
        type: selectedType,
        name: file.name,
        mime_type: file.type || "application/octet-stream",
        size_bytes: file.size,
      })
      if (!result.ok || !result.document) {
        toast.error(result.error ?? "Failed to upload document")
        return
      }

      const created = result.document
      createdId = created.id

      // Upload the bytes straight to the backend-provided URL. In local mode
      // this is a multipart POST to `/documents/{id}/upload`; the API client
      // (server-side only) is intentionally not used here.
      if (created.upload_url) {
        const token = await getToken()
        const uploadRes = await fetch(resolveUploadUrl(created.upload_url), {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
          body: buildUploadBody(file),
        })
        if (!uploadRes.ok) {
          const detail = await uploadRes.text().catch(() => "")
          throw new Error(
            `Upload failed: ${uploadRes.status} ${uploadRes.statusText}${
              detail ? ` — ${detail}` : ""
            }`,
          )
        }
      }

      setDocuments((prev) => [created, ...prev])
      toast.success("Document uploaded")
    } catch (error) {
      // Best-effort cleanup of orphaned metadata when the byte upload fails.
      if (createdId) {
        await deleteDocument(createdId, applicationId).catch(() => {})
      }
      toast.error(error instanceof Error ? error.message : "Failed to upload document")
    } finally {
      setUploading(false)
    }
  }

  async function handleDelete(id: string) {
    setDeletingId(id)
    try {
      const result = await deleteDocument(id, applicationId)
      if (result.ok) {
        setDocuments((prev) => prev.filter((doc) => doc.id !== id))
        toast.success("Document deleted")
      } else {
        toast.error(result.error ?? "Failed to delete document")
      }
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Documents</CardTitle>
        <CardDescription>
          Resumes, cover letters, and other files attached to this application.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Select
            value={selectedType}
            onValueChange={(value) => setSelectedType(value as DocumentType)}
          >
            <SelectTrigger className="w-[180px]" aria-label="Document type">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {DOCUMENT_TYPE_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={() => inputRef.current?.click()} disabled={uploading}>
            {uploading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Uploading…
              </>
            ) : (
              <>
                <Upload className="h-4 w-4" />
                Upload
              </>
            )}
          </Button>
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            accept=".pdf,.doc,.docx,.txt,.md,.rtf"
            onChange={handleFileSelected}
          />
        </div>

        {documents.length === 0 ? (
          <p className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
            No documents yet. Upload a resume or cover letter to get started.
          </p>
        ) : (
          <div className="overflow-hidden rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Added</TableHead>
                  <TableHead className="w-[72px] text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell className="font-medium">
                      <span className="flex items-center gap-2">
                        <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                        <span className="truncate">{doc.name}</span>
                      </span>
                    </TableCell>
                    <TableCell>
                      <DocumentTypeBadge type={doc.type} />
                    </TableCell>
                    <TableCell>{formatBytes(doc.size_bytes)}</TableCell>
                    <TableCell>{formatDate(doc.created_at)}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(doc.id)}
                        disabled={deletingId === doc.id || uploading}
                      >
                        {deletingId === doc.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                        <span className="sr-only">Delete {doc.name}</span>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function DocumentTypeBadge({ type }: { type: DocumentType }) {
  switch (type) {
    case "resume":
      return <Badge>Resume</Badge>
    case "cover_letter":
      return (
        <Badge className="border-blue-500/30 bg-blue-500/10 text-blue-700 dark:border-blue-400/30 dark:text-blue-300">
          Cover letter
        </Badge>
      )
    case "offer_letter":
      return (
        <Badge className="border-green-500/30 bg-green-500/10 text-green-700 dark:border-green-400/30 dark:text-green-400">
          Offer letter
        </Badge>
      )
    case "other":
      return <Badge variant="outline">Other</Badge>
  }
}

/** Build the multipart body for a local-mode document upload. */
function buildUploadBody(file: File): FormData {
  const formData = new FormData()
  formData.append("file", file)
  return formData
}

/**
 * Resolve a backend-provided upload URL. Absolute URLs (signed storage URLs or
 * fully-qualified backend paths) are used verbatim; relative paths (local-mode
 * endpoints like `/documents/{id}/upload`) are prefixed with the public API base.
 */
function resolveUploadUrl(uploadUrl: string): string {
  if (/^https?:\/\//i.test(uploadUrl)) return uploadUrl
  const base = process.env.NEXT_PUBLIC_API_URL ?? ""
  return `${base}${uploadUrl.startsWith("/") ? "" : "/"}${uploadUrl}`
}

function formatBytes(bytes: number | null | undefined): string {
  if (bytes == null || bytes <= 0) return "—"
  const units = ["B", "KB", "MB", "GB"]
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const value = bytes / Math.pow(1024, exponent)
  return `${value.toFixed(exponent === 0 ? 0 : 1)} ${units[exponent]}`
}

function formatDate(value: string | null): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })
}
