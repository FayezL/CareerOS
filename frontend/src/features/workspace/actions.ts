"use server"

import { revalidatePath } from "next/cache"

import {
  createTimelineEvent as apiCreateTimelineEvent,
  deleteTimelineEvent as apiDeleteTimelineEvent,
} from "@/services/api-client"
import type { TimelineEventCreate, TimelineEventType } from "@/types"

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

function buildTimelineEventPayload(formData: FormData): Partial<TimelineEventCreate> {
  const payload: Partial<TimelineEventCreate> = {
    application_id: formData.get("application_id") as string,
    event_type: (formData.get("event_type") as TimelineEventType) || "NOTE",
  }

  const summary = textValue(formData, "summary")
  if (summary) payload.summary = summary

  const note = textValue(formData, "note")
  if (note) payload.note = note

  const importance = textValue(formData, "importance") as "NORMAL" | "HIGH" | "CRITICAL"
  if (importance && ["NORMAL", "HIGH", "CRITICAL"].includes(importance)) {
    payload.importance = importance
  }

  const source = textValue(formData, "source")
  if (source) payload.source = source

  const rejection_reason_category = textValue(formData, "rejection_reason_category")
  if (rejection_reason_category) payload.rejection_reason_category = rejection_reason_category

  return payload
}

export async function createTimelineEvent(formData: FormData): Promise<ActionResult> {
  try {
    const payload = buildTimelineEventPayload(formData) as TimelineEventCreate
    await apiCreateTimelineEvent(payload)

    revalidatePath("/workspace")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function deleteTimelineEvent(id: string): Promise<ActionResult> {
  try {
    await apiDeleteTimelineEvent(id)
    revalidatePath("/workspace")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}
