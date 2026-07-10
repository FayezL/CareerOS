import { auth } from "@clerk/nextjs/server"
import { getEnv } from "@/lib/env"
import type {
  AIResult,
  AnalyticsFunnel,
  AnalyticsOverTime,
  AnalyticsSummary,
  Application,
  Company,
  Contact,
  CoverLetterRequest,
  Document,
  Interview,
  InterviewPrepRequest,
  Note,
  PageOut,
  PipelineStage,
  Reminder,
  StageHistory,
  Subscription,
  TailorResumeRequest,
} from "@/lib/types"

/**
 * Server-side fetch helper that forwards the caller's Clerk session JWT as a
 * Bearer token to the FastAPI backend.
 *
 * Must be called from a Server Component, Route Handler, or Server Action
 * (anywhere Clerk's `auth()` is available).
 */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const { getToken } = await auth()
  const token = await getToken()
  const base = getEnv().NEXT_PUBLIC_API_URL

  const headers = new Headers(init?.headers)
  headers.set("Accept", "application/json")
  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  const res = await fetch(`${base}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  })

  if (!res.ok) {
    const body = await res.text().catch(() => "")
    throw new Error(
      `API request failed: ${res.status} ${res.statusText}${body ? ` — ${body}` : ""}`,
    )
  }

  // Empty responses (e.g. `204 No Content`) or non-JSON bodies have no payload
  // to parse — resolve to `undefined` and let the caller cast as needed.
  if (res.status === 204) {
    return undefined as T
  }
  const contentType = res.headers.get("content-type") ?? ""
  if (!contentType.includes("application/json")) {
    return undefined as T
  }

  return res.json() as Promise<T>
}

/**
 * Normalize a list response that may be either a paginated `PageOut<T>` envelope
 * or a bare `T[]` array into a plain array. Keeps the UI resilient to backend
 * list-shape changes.
 */
function unwrapList<T>(data: PageOut<T> | T[]): T[] {
  return Array.isArray(data) ? data : data.items
}

/** Fetch the authenticated user's companies. */
export async function listCompanies(): Promise<Company[]> {
  const data = await apiFetch<PageOut<Company> | Company[]>("/companies")
  return unwrapList(data)
}

/** Fetch the authenticated user's applications. */
export async function listApplications(): Promise<Application[]> {
  const data = await apiFetch<PageOut<Application> | Application[]>("/applications")
  return unwrapList(data)
}

/** Fetch a single application by id (embeds company and current stage). */
export async function getApplication(id: string): Promise<Application> {
  return apiFetch<Application>(`/applications/${id}`)
}

/** Fetch the stage-change timeline for an application, oldest first. */
export async function listStageHistory(applicationId: string): Promise<StageHistory[]> {
  const data = await apiFetch<PageOut<StageHistory> | StageHistory[]>(
    `/applications/${applicationId}/history`,
  )
  return unwrapList(data)
}

/** Fetch the user's pipeline stages, ordered by position. */
export async function listStages(): Promise<PipelineStage[]> {
  const data = await apiFetch<PageOut<PipelineStage> | PipelineStage[]>("/pipeline-stages")
  return unwrapList(data)
}

/** Fetch the user's contacts. */
export async function listContacts(): Promise<Contact[]> {
  const data = await apiFetch<PageOut<Contact> | Contact[]>("/contacts")
  return unwrapList(data)
}

/** Fetch the user's interviews. */
export async function listInterviews(): Promise<Interview[]> {
  const data = await apiFetch<PageOut<Interview> | Interview[]>("/interviews")
  return unwrapList(data)
}

/** Fetch notes attached to a given application. */
export async function listNotes(applicationId: string): Promise<Note[]> {
  const data = await apiFetch<PageOut<Note> | Note[]>(
    `/notes?application_id=${encodeURIComponent(applicationId)}`,
  )
  return unwrapList(data)
}
