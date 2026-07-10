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

function compact(entries: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(Object.entries(entries).filter(([, v]) => v !== undefined))
}

function buildContactPayload(formData: FormData): Record<string, unknown> {
  return compact({
    company_id: textValue(formData, "company_id"),
    name: textValue(formData, "name"),
    email: textValue(formData, "email"),
    linkedin_url: textValue(formData, "linkedin_url"),
    role: textValue(formData, "role"),
  })
}

export async function createContact(formData: FormData): Promise<ActionResult> {
  const payload = buildContactPayload(formData)
  if (!payload.name) {
    return { ok: false, error: "Name is required." }
  }
  try {
    await apiFetch("/contacts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    revalidatePath("/contacts")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function updateContact(id: string, formData: FormData): Promise<ActionResult> {
  const payload = buildContactPayload(formData)
  if (!payload.name) {
    return { ok: false, error: "Name is required." }
  }
  try {
    await apiFetch(`/contacts/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    revalidatePath("/contacts")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function deleteContact(id: string): Promise<ActionResult> {
  try {
    await apiFetch(`/contacts/${id}`, { method: "DELETE" })
    revalidatePath("/contacts")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}
