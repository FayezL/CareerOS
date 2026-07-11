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

function buildReminderPayload(formData: FormData): Record<string, unknown> {
  return compact({
    application_id: textValue(formData, "application_id"),
    interview_id: textValue(formData, "interview_id"),
    title: textValue(formData, "title"),
    due_at: textValue(formData, "due_at"),
  })
}

export async function createReminder(formData: FormData): Promise<ActionResult> {
  const payload = buildReminderPayload(formData)
  if (!payload.title) {
    return { ok: false, error: "Title is required." }
  }
  if (!payload.due_at) {
    return { ok: false, error: "A due date is required." }
  }
  try {
    await apiFetch("/reminders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    revalidatePath("/reminders")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function updateReminder(id: string, formData: FormData): Promise<ActionResult> {
  const payload = buildReminderPayload(formData)
  if (!payload.title) {
    return { ok: false, error: "Title is required." }
  }
  if (!payload.due_at) {
    return { ok: false, error: "A due date is required." }
  }
  try {
    await apiFetch(`/reminders/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    revalidatePath("/reminders")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function deleteReminder(id: string): Promise<ActionResult> {
  try {
    await apiFetch(`/reminders/${id}`, { method: "DELETE" })
    revalidatePath("/reminders")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function completeReminder(id: string): Promise<ActionResult> {
  try {
    await apiFetch(`/reminders/${id}/complete`, { method: "POST" })
    revalidatePath("/reminders")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function snoozeReminder(id: string, dueAt: string): Promise<ActionResult> {
  if (!dueAt) {
    return { ok: false, error: "A new due date is required." }
  }
  try {
    await apiFetch(`/reminders/${id}/snooze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ due_at: dueAt }),
    })
    revalidatePath("/reminders")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}
