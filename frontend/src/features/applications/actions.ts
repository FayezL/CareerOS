"use server"

import { revalidatePath } from "next/cache"

import { apiFetch } from "@/lib/api-client"

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

function buildApplicationPayload(formData: FormData): Record<string, unknown> {
  return compact({
    company_id: textValue(formData, "company_id"),
    role_title: textValue(formData, "role_title"),
    status: textValue(formData, "status"),
    job_url: textValue(formData, "job_url"),
    source: textValue(formData, "source"),
    salary_min: numberValue(formData, "salary_min"),
    salary_max: numberValue(formData, "salary_max"),
    salary_currency: textValue(formData, "salary_currency"),
    applied_at: textValue(formData, "applied_at"),
    job_description: textValue(formData, "job_description"),
  })
}

export async function createApplication(formData: FormData): Promise<ActionResult> {
  const payload = buildApplicationPayload(formData)
  if (!payload.role_title) {
    return { ok: false, error: "Role title is required." }
  }
  if (!payload.company_id) {
    return { ok: false, error: "Please choose a company." }
  }
  try {
    await apiFetch("/applications", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    revalidatePath("/applications")
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
  if (!payload.company_id) {
    return { ok: false, error: "Please choose a company." }
  }
  try {
    await apiFetch(`/applications/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    revalidatePath("/applications")
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
