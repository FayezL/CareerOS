"use client"

import { useRef, useState, type ChangeEvent } from "react"
import { useAuth } from "@clerk/nextjs"
import { FileText, Loader2, Trash2, Upload } from "lucide-react"
import { toast } from "sonner"

import type { Document, DocumentType } from "@/types"
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

import { createDocumentMetadata, createDocumentRevision, deleteDocument } from "./actions"
import { DOCUMENT_TYPE_OPTIONS, groupDocuments, type DocumentGroup } from "./document-groups"

type DocumentsPanelProps = {
  applicationId: string
  initial: Document[]
}

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
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set())
  const [addingVersionTo, setAddingVersionTo] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const versionInputRef = useRef<HTMLInputElement>(null)

  const groups = groupDocuments(documents)

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

  function toggleGroup(rootId: string) {
    setExpandedGroups((prev) => {
      const next = new Set(prev)
      if (next.has(rootId)) {
        next.delete(rootId)
      } else {
        next.add(rootId)
      }
      return next
    })
  }

  function handleAddVersion(rootId: string) {
    versionInputRef.current?.click()
    setAddingVersionTo(rootId)
  }

  async function handleVersionFileSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    // Reset so picking the same file again re-triggers `onChange`.
    event.target.value = ""
    if (!file || !addingVersionTo) return

    setUploading(true)
    let createdId: string | null = null
    try {
      const result = await createDocumentRevision({
        rootId: addingVersionTo,
        name: file.name,
        mime_type: file.type || "application/octet-stream",
        size_bytes: file.size,
      })
      if (!result.ok || !result.document) {
        toast.error(result.error ?? "Failed to create revision")
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

      setDocuments((prev) => [...prev, created])
      toast.success("New version added")
    } catch (error) {
      // Best-effort cleanup of orphaned metadata when the byte upload fails.
      if (createdId) {
        await deleteDocument(createdId, applicationId).catch(() => {})
      }
      toast.error(error instanceof Error ? error.message : "Failed to add version")
    } finally {
      setUploading(false)
      setAddingVersionTo(null)
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

        {groups.length === 0 ? (
          <p className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
            No documents yet. Upload a resume or cover letter to get started.
          </p>
        ) : (
          <div className="space-y-2">
            {groups.map((group) => (
              <GroupRow
                key={group.rootId}
                group={group}
                isExpanded={expandedGroups.has(group.rootId)}
                onToggle={() => toggleGroup(group.rootId)}
                onAddVersion={() => handleAddVersion(group.rootId)}
                onDelete={handleDelete}
                deletingId={deletingId}
                uploading={uploading}
              />
            ))}
          </div>
        )}
      </CardContent>
      <input
        ref={versionInputRef}
        type="file"
        className="hidden"
        accept=".pdf,.doc,.docx,.txt,.md,.rtf"
        onChange={handleVersionFileSelected}
      />
    </Card>
  )
}

function GroupRow({
  group,
  isExpanded,
  onToggle,
  onAddVersion,
  onDelete,
  deletingId,
  uploading,
}: {
  group: DocumentGroup
  isExpanded: boolean
  onToggle: () => void
  onAddVersion: () => void
  onDelete: (id: string) => void
  deletingId: string | null
  uploading: boolean
}) {
  return (
    <div className="overflow-hidden rounded-lg border">
      <div className="flex items-center justify-between border-b bg-muted/50 px-4 py-3">
        <button
          onClick={onToggle}
          className="flex flex-1 items-center gap-3 text-left"
          aria-expanded={isExpanded}
        >
          <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
          <span className="flex-1 font-medium">{group.latest.name}</span>
          <span className="text-sm text-muted-foreground">v{group.latest.version ?? 1}</span>
          <Badge variant="secondary">
            {group.count} {group.count === 1 ? "version" : "versions"}
          </Badge>
        </button>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={onAddVersion} disabled={uploading}>
            <Upload className="h-3 w-3 mr-1" />
            Add version
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onDelete(group.latest.id)}
            disabled={deletingId === group.latest.id || uploading}
          >
            {deletingId === group.latest.id ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="h-4 w-4" />
            )}
            <span className="sr-only">Delete {group.latest.name}</span>
          </Button>
        </div>
      </div>
      {isExpanded && (
        <div className="divide-y">
          {group.revisions.map((doc) => (
            <div key={doc.id} className="flex items-center justify-between px-4 py-2 text-sm">
              <div className="flex items-center gap-3">
                <div className="w-4" />
                <span className="text-muted-foreground">v{doc.version ?? 1}</span>
                <span>{doc.name}</span>
                {doc.version_label && (
                  <Badge variant="outline" className="text-xs">
                    {doc.version_label}
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-4 text-muted-foreground">
                <span>{formatBytes(doc.size_bytes)}</span>
                <span>{formatDate(doc.created_at)}</span>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => onDelete(doc.id)}
                  disabled={deletingId === doc.id || uploading}
                  className="h-6 w-6"
                >
                  {deletingId === doc.id ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <Trash2 className="h-3 w-3" />
                  )}
                  <span className="sr-only">Delete version {doc.version ?? 1}</span>
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
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
