"use server"

import { revalidatePath } from "next/cache"

import { apiFetch } from "@/services/api-client"

export type ActionResult = { ok: boolean; error?: string }

function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) return error.message
  return "Something went wrong. Please try again."
}

function textValue(formData: FormData, key: string): string | undefined {
  const raw = formData.get(key)
  if (raw === null) return undefined
  const value = String(raw).trim()
  return value === "" ? undefined : value
}

function numberValue(formData: FormData, key: string): number | undefined {
  const value = textValue(formData, key)
  if (value === undefined) return undefined
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : undefined
}

function compact(entries: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(Object.entries(entries).filter(([, v]) => v !== undefined))
}

function tagValues(formData: FormData): string[] {
  // FormData emits one entry per hidden input named "tags"; collect all
  // non-empty values and dedupe case-insensitively (the backend re-resolves,
  // but de-duping here keeps the request clean).
  const seen = new Set<string>()
  const out: string[] = []
  for (const value of formData.getAll("tags")) {
    const name = String(value).trim()
    if (!name) continue
    const key = name.toLowerCase()
    if (seen.has(key)) continue
    seen.add(key)
    out.push(name)
  }
  return out
}

function buildApplicationPayload(formData: FormData): Record<string, unknown> {
  return compact({
    company_id: textValue(formData, "company_id"),
    company_name: textValue(formData, "company_name"),
    role_title: textValue(formData, "role_title"),
    status: textValue(formData, "status"),
    job_url: textValue(formData, "job_url"),
    source: textValue(formData, "source"),
    salary_min: numberValue(formData, "salary_min"),
    salary_max: numberValue(formData, "salary_max"),
    salary_currency: textValue(formData, "salary_currency"),
    applied_at: textValue(formData, "applied_at"),
    job_description: textValue(formData, "job_description"),
    rejection_reason: textValue(formData, "rejection_reason"),
    tags: tagValues(formData),
  })
}

function validateCompanyRef(payload: Record<string, unknown>): string | null {
  if (payload.company_id && payload.company_name) {
    return "Provide either an existing company or a new name, not both."
  }
  if (!payload.company_id && !payload.company_name) {
    return "Please choose or type a company."
  }
  return null
}

export async function createApplication(formData: FormData): Promise<ActionResult> {
  const payload = buildApplicationPayload(formData)
  if (!payload.role_title) {
    return { ok: false, error: "Role title is required." }
  }
  const companyError = validateCompanyRef(payload)
  if (companyError) return { ok: false, error: companyError }
  try {
    await apiFetch("/applications", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    revalidatePath("/applications")
    revalidatePath("/companies")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function updateApplication(id: string, formData: FormData): Promise<ActionResult> {
  const payload = buildApplicationPayload(formData)
  if (!payload.role_title) {
    return { ok: false, error: "Role title is required." }
  }
  const companyError = validateCompanyRef(payload)
  if (companyError) return { ok: false, error: companyError }
  try {
    await apiFetch(`/applications/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    revalidatePath("/applications")
    revalidatePath("/companies")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function deleteApplication(id: string): Promise<ActionResult> {
  try {
    await apiFetch(`/applications/${id}`, { method: "DELETE" })
    revalidatePath("/applications")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

/**
 * Patch ONLY the rejection fields on an application. The backend uses
 * `exclude_unset=True`, so omitting other fields leaves them untouched.
 *
 * Pass `null` (explicit) for either field to clear it; pass `undefined` to
 * leave the field at its current value.
 */
export async function updateRejectionDetails(
  id: string,
  fields: {
    rejection_reason_category?: string | null
    rejection_reason?: string | null
  },
): Promise<ActionResult> {
  // Build a payload that only carries keys the caller touched. We send the
  // keys explicitly so the backend clears a field when the value is null.
  const payload: Record<string, unknown> = {}
  if ("rejection_reason_category" in fields) {
    payload.rejection_reason_category = fields.rejection_reason_category || null
  }
  if ("rejection_reason" in fields) {
    const reason = fields.rejection_reason?.trim() || null
    if (reason && reason.length > 255) {
      return { ok: false, error: "Rejection reason must be 255 characters or fewer." }
    }
    payload.rejection_reason = reason
  }
  try {
    await apiFetch(`/applications/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    revalidatePath("/applications")
    revalidatePath(`/applications/${id}`)
    revalidatePath("/pipeline")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}
