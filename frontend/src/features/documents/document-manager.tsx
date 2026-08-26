"use client"

import { useRef, useState, type ChangeEvent } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@clerk/nextjs"
import { ChevronDown, ChevronRight, FileText, Loader2, Plus, Upload } from "lucide-react"
import { toast } from "sonner"

import type { Document, DocumentType } from "@/types"
import { DOCUMENT_TYPE_OPTIONS, documentTypeLabel } from "./document-groups"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

type DocumentManagerProps = {
  initial: Document[]
  nextCursor: string | null
  initialType?: DocumentType
}

export function DocumentManager({ initial, nextCursor, initialType }: DocumentManagerProps) {
  const router = useRouter()
  const { getToken } = useAuth()
  const [documents, setDocuments] = useState<Document[]>(initial)
  const [currentCursor, setCurrentCursor] = useState<string | null>(nextCursor)
  const [activeType, setActiveType] = useState<DocumentType | undefined>(initialType)
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set())
  const [revisionsCache, setRevisionsCache] = useState<Map<string, Document[]>>(new Map())
  const [loadingMore, setLoadingMore] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [uploadType, setUploadType] = useState<DocumentType>("resume")
  const [uploadVersionLabel, setUploadVersionLabel] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)

  function handleTypeFilter(type: DocumentType | undefined) {
    setActiveType(type)
    router.push(type ? `/documents?type=${type}` : "/documents")
  }

  async function handleExpand(doc: Document) {
    const rootId = doc.parent_document_id ?? doc.id
    const newExpanded = new Set(expandedGroups)

    if (newExpanded.has(rootId)) {
      newExpanded.delete(rootId)
    } else {
      newExpanded.add(rootId)
      if (!revisionsCache.has(rootId)) {
        try {
          const token = await getToken()
          const revisions = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/documents/${rootId}/revisions`,
            {
              headers: token ? { Authorization: `Bearer ${token}` } : {},
            },
          ).then((res) => res.json())
          setRevisionsCache((prev) => new Map(prev).set(rootId, revisions))
        } catch {
          toast.error("Failed to load revisions")
        }
      }
    }

    setExpandedGroups(newExpanded)
  }

  async function handleLoadMore() {
    if (!currentCursor || loadingMore) return

    setLoadingMore(true)
    try {
      const token = await getToken()
      const params = new URLSearchParams()
      if (activeType) params.set("type", activeType)
      if (currentCursor) params.set("cursor", currentCursor)

      const page = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/documents?${params.toString()}`,
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        },
      ).then((res) => res.json())
      setDocuments((prev) => [...prev, ...page.items])
      setCurrentCursor(page.next_cursor)
    } catch {
      toast.error("Failed to load more documents")
    } finally {
      setLoadingMore(false)
    }
  }

  async function handleFileSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ""
    if (!file) return

    setUploading(true)
    let createdId: string | null = null
    let token: string | null = null
    try {
      token = await getToken()
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/documents`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          type: uploadType,
          name: file.name,
          mime_type: file.type || "application/octet-stream",
          size_bytes: file.size,
          version_label: uploadVersionLabel || undefined,
        }),
      })

      if (!res.ok) {
        const error = await res.text()
        throw new Error(error || "Failed to create document")
      }

      const created: Document = await res.json()
      createdId = created.id

      if (created.upload_url) {
        const uploadRes = await fetch(resolveUploadUrl(created.upload_url), {
          method: created.upload_method || "POST",
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...created.upload_headers,
          },
          body: buildUploadBody(file),
        })

        if (!uploadRes.ok) {
          const detail = await uploadRes.text().catch(() => "")
          throw new Error(`Upload failed: ${uploadRes.status} ${detail}`)
        }
      }

      setDocuments((prev) => [created, ...prev])
      toast.success("Document uploaded")
      setUploadDialogOpen(false)
      setUploadVersionLabel("")
    } catch (error) {
      if (createdId) {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/documents/${createdId}`, {
          method: "DELETE",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }).catch(() => {})
      }
      toast.error(error instanceof Error ? error.message : "Failed to upload document")
    } finally {
      setUploading(false)
    }
  }

  async function handleAddVersion(doc: Document, event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ""
    if (!file) return

    setUploading(true)
    let createdId: string | null = null
    let token: string | null = null
    try {
      token = await getToken()
      const rootId = doc.parent_document_id ?? doc.id
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/documents/${rootId}/revisions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: file.name,
          mime_type: file.type || "application/octet-stream",
          size_bytes: file.size,
        }),
      })

      if (!res.ok) {
        const error = await res.text()
        throw new Error(error || "Failed to create revision")
      }

      const created: Document = await res.json()
      createdId = created.id

      if (created.upload_url) {
        const uploadRes = await fetch(resolveUploadUrl(created.upload_url), {
          method: created.upload_method || "POST",
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...created.upload_headers,
          },
          body: buildUploadBody(file),
        })

        if (!uploadRes.ok) {
          const detail = await uploadRes.text().catch(() => "")
          throw new Error(`Upload failed: ${uploadRes.status} ${detail}`)
        }
      }

      router.refresh()
      toast.success("New version added")
    } catch (error) {
      if (createdId) {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/documents/${createdId}`, {
          method: "DELETE",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }).catch(() => {})
      }
      toast.error(error instanceof Error ? error.message : "Failed to add version")
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Documents</h1>
          <p className="text-sm text-muted-foreground">
            Manage your resumes, cover letters, and supporting files.
          </p>
        </div>
        <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Upload
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Upload document</DialogTitle>
              <DialogDescription>Add a new document to your library.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="type">Type</Label>
                <Select
                  value={uploadType}
                  onValueChange={(value) => setUploadType(value as DocumentType)}
                >
                  <SelectTrigger id="type">
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
              </div>
              <div className="space-y-2">
                <Label htmlFor="versionLabel">Version label (optional)</Label>
                <Input
                  id="versionLabel"
                  placeholder="e.g., v2.0, Updated 2024"
                  value={uploadVersionLabel}
                  onChange={(e) => setUploadVersionLabel(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button onClick={() => fileInputRef.current?.click()} disabled={uploading}>
                {uploading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading…
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Choose file
                  </>
                )}
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".pdf,.doc,.docx,.txt,.md,.rtf"
                onChange={handleFileSelected}
              />
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex flex-wrap gap-2" role="tablist" aria-label="Document types">
        <button
          type="button"
          role="tab"
          aria-selected={!activeType}
          onClick={() => handleTypeFilter(undefined)}
          className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
            !activeType
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground hover:bg-muted/80"
          }`}
        >
          All
        </button>
        {DOCUMENT_TYPE_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={activeType === option.value}
            onClick={() => handleTypeFilter(option.value)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
              activeType === option.value
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground hover:bg-muted/80"
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      {documents.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="mb-4 h-12 w-12 text-muted-foreground" />
            <h3 className="text-lg font-semibold">No documents yet</h3>
            <p className="mb-4 text-center text-sm text-muted-foreground">
              Upload your first resume to get started.
            </p>
            <Button onClick={() => setUploadDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Upload document
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <ul className="space-y-3" role="list">
            {documents.map((doc) => {
              const rootId = doc.parent_document_id ?? doc.id
              const isExpanded = expandedGroups.has(rootId)
              const revisions = revisionsCache.get(rootId) || []

              return (
                <li key={doc.id}>
                  <Card>
                    <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                      <div className="space-y-1">
                        <CardTitle className="flex items-center gap-2 text-base">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          {doc.name}
                        </CardTitle>
                        <CardDescription className="flex items-center gap-2">
                          <Badge variant="outline">{documentTypeLabel(doc.type)}</Badge>
                          {doc.version_label && <span>{doc.version_label}</span>}
                          <span>v{doc.version}</span>
                          {doc.revisions_count && doc.revisions_count > 1 && (
                            <span>({doc.revisions_count} versions)</span>
                          )}
                        </CardDescription>
                      </div>
                      <div className="flex items-center gap-2">
                        {doc.revisions_count && doc.revisions_count > 1 && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleExpand(doc)}
                            aria-expanded={isExpanded}
                            aria-controls={`revisions-${rootId}`}
                          >
                            {isExpanded ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                            <span className="sr-only">
                              {isExpanded ? "Hide revisions" : "Show revisions"}
                            </span>
                          </Button>
                        )}
                        <div className="relative">
                          <input
                            type="file"
                            className="absolute inset-0 opacity-0 cursor-pointer"
                            accept=".pdf,.doc,.docx,.txt,.md,.rtf"
                            onChange={(e) => handleAddVersion(doc, e)}
                            disabled={uploading}
                          />
                          <Button variant="outline" size="sm" disabled={uploading}>
                            {uploading ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Plus className="h-4 w-4" />
                            )}
                            <span className="ml-2">Add version</span>
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="text-sm text-muted-foreground">
                      Updated {new Date(doc.updated_at).toLocaleDateString()}
                    </CardContent>
                  </Card>
                  {isExpanded && revisions.length > 0 && (
                    <div
                      id={`revisions-${rootId}`}
                      className="ml-6 mt-2 space-y-2 border-l-2 border-muted pl-4"
                    >
                      {revisions.map((rev) => (
                        <div key={rev.id} className="flex items-center justify-between text-sm">
                          <div>
                            <span className="font-medium">v{rev.version}</span>
                            {rev.version_label && <span className="ml-2">{rev.version_label}</span>}
                          </div>
                          <div className="text-muted-foreground">
                            {new Date(rev.updated_at).toLocaleDateString()}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </li>
              )
            })}
          </ul>

          {currentCursor && (
            <div className="flex justify-center">
              <Button variant="outline" onClick={handleLoadMore} disabled={loadingMore}>
                {loadingMore ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Loading…
                  </>
                ) : (
                  "Load more"
                )}
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function buildUploadBody(file: File): FormData {
  const formData = new FormData()
  formData.append("file", file)
  return formData
}

function resolveUploadUrl(uploadUrl: string): string {
  if (/^https?:\/\//i.test(uploadUrl)) return uploadUrl
  const base = process.env.NEXT_PUBLIC_API_URL ?? ""
  return `${base}${uploadUrl.startsWith("/") ? "" : "/"}${uploadUrl}`
}
