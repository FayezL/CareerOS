/** Shared helpers for the backend's two-step document upload flow. */

/** Build the multipart body for a local-mode document upload. */
export function buildUploadBody(file: File): FormData {
  const formData = new FormData()
  formData.append("file", file)
  return formData
}

/**
 * Resolve a backend-provided upload URL. Absolute URLs (signed storage URLs or
 * fully-qualified backend paths) are used verbatim; relative paths (local-mode
 * endpoints like `/documents/{id}/upload`) are prefixed with the public API base.
 */
export function resolveUploadUrl(uploadUrl: string): string {
  if (/^https?:\/\//i.test(uploadUrl)) return uploadUrl
  const base = process.env.NEXT_PUBLIC_API_URL ?? ""
  return `${base}${uploadUrl.startsWith("/") ? "" : "/"}${uploadUrl}`
}
