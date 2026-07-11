"use server"

import { revalidatePath } from "next/cache"

import { apiFetch } from "@/services/api-client"

export type ActionResult = { ok: boolean; error?: string }

function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) return error.message
  return "Something went wrong. Please try again."
}

/** Read a trimmed string field, returning `undefined` when empty/absent. */
function textValue(formData: FormData, key: string): string | undefined {
  const raw = formData.get(key)
  if (raw === null) return undefined
  const value = String(raw).trim()
  return value === "" ? undefined : value
}

/** Build a JSON payload, dropping any omitted (undefined) fields. */
function compact(entries: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(Object.entries(entries).filter(([, v]) => v !== undefined))
}

function buildCompanyPayload(formData: FormData): Record<string, unknown> {
  return compact({
    name: textValue(formData, "name"),
    website: textValue(formData, "website"),
    industry: textValue(formData, "industry"),
    size: textValue(formData, "size"),
    location: textValue(formData, "location"),
    linkedin_url: textValue(formData, "linkedin_url"),
    notes: textValue(formData, "notes"),
  })
}

export async function createCompany(formData: FormData): Promise<ActionResult> {
  const payload = buildCompanyPayload(formData)
  if (!payload.name) {
    return { ok: false, error: "Name is required." }
  }
  try {
    await apiFetch("/companies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    revalidatePath("/companies")
    revalidatePath("/applications")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function updateCompany(id: string, formData: FormData): Promise<ActionResult> {
  const payload = buildCompanyPayload(formData)
  if (!payload.name) {
    return { ok: false, error: "Name is required." }
  }
  try {
    await apiFetch(`/companies/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    revalidatePath("/companies")
    revalidatePath("/applications")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function deleteCompany(id: string): Promise<ActionResult> {
  try {
    await apiFetch(`/companies/${id}`, { method: "DELETE" })
    revalidatePath("/companies")
    revalidatePath("/applications")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}
