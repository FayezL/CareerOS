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

function buildInterviewPayload(formData: FormData): Record<string, unknown> {
  return compact({
    application_id: textValue(formData, "application_id"),
    type: textValue(formData, "type"),
    scheduled_at: textValue(formData, "scheduled_at"),
    duration_minutes: numberValue(formData, "duration_minutes"),
    location: textValue(formData, "location"),
    interviewer_contact_id: textValue(formData, "interviewer_contact_id"),
    notes: textValue(formData, "notes"),
  })
}

export async function createInterview(formData: FormData): Promise<ActionResult> {
  const payload = buildInterviewPayload(formData)
  if (!payload.application_id) {
    return { ok: false, error: "Please choose an application." }
  }
  if (!payload.scheduled_at) {
    return { ok: false, error: "Scheduled time is required." }
  }
  try {
    await apiFetch("/interviews", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    revalidatePath("/interviews")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function updateInterview(id: string, formData: FormData): Promise<ActionResult> {
  const payload = buildInterviewPayload(formData)
  if (!payload.application_id) {
    return { ok: false, error: "Please choose an application." }
  }
  if (!payload.scheduled_at) {
    return { ok: false, error: "Scheduled time is required." }
  }
  try {
    await apiFetch(`/interviews/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    revalidatePath("/interviews")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function deleteInterview(id: string): Promise<ActionResult> {
  try {
    await apiFetch(`/interviews/${id}`, { method: "DELETE" })
    revalidatePath("/interviews")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}
