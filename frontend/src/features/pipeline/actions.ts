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

function compact(entries: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(Object.entries(entries).filter(([, v]) => v !== undefined))
}

function buildStagePayload(formData: FormData): Record<string, unknown> {
  return compact({
    name: textValue(formData, "name"),
    color: textValue(formData, "color"),
  })
}

export async function createStage(formData: FormData): Promise<ActionResult> {
  const payload = buildStagePayload(formData)
  if (!payload.name) {
    return { ok: false, error: "Stage name is required." }
  }
  try {
    await apiFetch("/pipeline-stages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    revalidatePath("/pipeline")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function updateStage(id: string, formData: FormData): Promise<ActionResult> {
  const payload = buildStagePayload(formData)
  if (!payload.name) {
    return { ok: false, error: "Stage name is required." }
  }
  try {
    await apiFetch(`/pipeline-stages/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    revalidatePath("/pipeline")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function deleteStage(id: string): Promise<ActionResult> {
  try {
    await apiFetch(`/pipeline-stages/${id}`, { method: "DELETE" })
    revalidatePath("/pipeline")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function reorderStages(stageIds: string[]): Promise<ActionResult> {
  try {
    await apiFetch("/pipeline-stages/reorder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ordered_ids: stageIds }),
    })
    revalidatePath("/pipeline")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function moveApplication(
  applicationId: string,
  toStageId: string,
  options?: {
    rejection_reason_category?: string
    rejection_reason?: string
  },
): Promise<ActionResult> {
  try {
    const body: Record<string, unknown> = { to_stage_id: toStageId }
    if (options?.rejection_reason_category) {
      body.rejection_reason_category = options.rejection_reason_category
    }
    if (options?.rejection_reason) {
      body.rejection_reason = options.rejection_reason
    }
    await apiFetch(`/applications/${applicationId}/move`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
    revalidatePath("/pipeline")
    revalidatePath(`/applications/${applicationId}`)
    revalidatePath("/applications")
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}
