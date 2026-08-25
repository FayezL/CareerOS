import type { Document, DocumentType } from "@/types"

/** One logical document: its root, all rows, and the newest representative. */
export type DocumentGroup = {
  rootId: string
  /** Every row of the group, oldest first (root first). */
  revisions: Document[]
  /** The newest row (what the grouped API returns as the list entry). */
  latest: Document
  /** 1 when the group has no revisions yet. */
  count: number
}

/**
 * Merge a flat list of document rows (any mix of roots and revisions, e.g.
 * from `include_revisions=true`) into grouped view models.
 * Rows whose parent is missing from the input are still surfaced under
 * their own rootId so nothing silently disappears.
 */
export function groupDocuments(documents: Document[]): DocumentGroup[] {
  const roots = new Map<string, Document>()
  const byRoot = new Map<string, Document[]>()

  for (const doc of documents) {
    const rootId = doc.parent_document_id ?? doc.id
    if (!doc.parent_document_id) roots.set(doc.id, doc)
    const list = byRoot.get(rootId)
    if (list) {
      list.push(doc)
    } else {
      byRoot.set(rootId, [doc])
    }
  }

  const groups: DocumentGroup[] = []
  for (const [rootId, revisions] of byRoot) {
    const sorted = [...revisions].sort(
      (a, b) =>
        (a.version ?? 1) - (b.version ?? 1) ||
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    )
    groups.push({
      rootId,
      revisions: sorted,
      latest: sorted[sorted.length - 1],
      count: sorted.length,
    })
  }

  // Newest groups first, by their representative row.
  return groups.sort(
    (a, b) => new Date(b.latest.created_at).getTime() - new Date(a.latest.created_at).getTime(),
  )
}

/** Human labels for the 6 document types (single source for chips + badges). */
export const DOCUMENT_TYPE_OPTIONS: { value: DocumentType; label: string }[] = [
  { value: "resume", label: "Resume" },
  { value: "cover_letter", label: "Cover letter" },
  { value: "certificate", label: "Certificate" },
  { value: "reference", label: "Reference" },
  { value: "visa", label: "Visa" },
  { value: "other", label: "Other" },
]

export function documentTypeLabel(type: DocumentType): string {
  return DOCUMENT_TYPE_OPTIONS.find((o) => o.value === type)?.label ?? "Other"
}
