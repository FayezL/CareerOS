import { auth } from "@clerk/nextjs/server"
import { getEnv } from "@/schemas/env"
import type {
  AnalyticsFunnel,
  AnalyticsOverTime,
  AnalyticsSummary,
  Application,
  Company,
  CompanyOption,
  Contact,
  Document,
  Interview,
  Note,
  PageOut,
  PipelineStage,
  Reminder,
  StageHistory,
} from "@/types"

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
  const env = getEnv()
  // Server-side fetches run INSIDE this container; use the internal backend URL
  // (Docker service hostname) when provided. The public URL is for the browser.
  const base = env.API_INTERNAL_URL ?? env.NEXT_PUBLIC_API_URL

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

/** Fetch a single company by id. */
export async function getCompany(id: string): Promise<Company> {
  return apiFetch<Company>(`/companies/${id}`)
}

/** Prefix-match autocomplete for the company picker (used by the combobox). */
export async function searchCompanies(query: string): Promise<CompanyOption[]> {
  const q = query.trim()
  if (!q) return []
  const data = await apiFetch<CompanyOption[]>(`/companies/search?q=${encodeURIComponent(q)}`)
  return data
}

/** Fetch the authenticated user's applications, optionally scoped to a company. */
export async function listApplications(params?: { companyId?: string }): Promise<Application[]> {
  const qs = params?.companyId ? `?company_id=${encodeURIComponent(params.companyId)}` : ""
  const data = await apiFetch<PageOut<Application> | Application[]>(`/applications${qs}`)
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

/** Fetch the user's contacts, optionally scoped to a company. */
export async function listContacts(params?: { companyId?: string }): Promise<Contact[]> {
  const qs = params?.companyId ? `?company_id=${encodeURIComponent(params.companyId)}` : ""
  const data = await apiFetch<PageOut<Contact> | Contact[]>(`/contacts${qs}`)
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

/** Fetch documents attached to a given application. */
export async function listDocuments(applicationId: string): Promise<Document[]> {
  const data = await apiFetch<PageOut<Document> | Document[]>(
    `/documents?application_id=${encodeURIComponent(applicationId)}`,
  )
  return unwrapList(data)
}

/**
 * Fetch the user's reminders.
 *
 * Pass `completed` to filter by completion state and `dueBefore` (an ISO 8601
 * timestamp) to limit to reminders due at or before that time. The backend
 * caps `limit` at 100.
 */
export async function listReminders(params?: {
  limit?: number
  dueBefore?: string
  completed?: boolean
}): Promise<Reminder[]> {
  const query = new URLSearchParams()
  if (params?.limit) query.set("limit", String(params.limit))
  if (params?.dueBefore) query.set("due_before", params.dueBefore)
  if (typeof params?.completed === "boolean") {
    query.set("completed", String(params.completed))
  }
  const qs = query.toString()
  const data = await apiFetch<PageOut<Reminder> | Reminder[]>(`/reminders${qs ? `?${qs}` : ""}`)
  return unwrapList(data)
}

/** Fetch headline analytics totals and the overall response rate. */
export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  return apiFetch<AnalyticsSummary>("/analytics/summary")
}

/** Fetch stage-by-stage funnel counts derived from stage history. */
export async function getAnalyticsFunnel(): Promise<AnalyticsFunnel> {
  return apiFetch<AnalyticsFunnel>("/analytics/funnel")
}

/**
 * Fetch applications-per-bucket within a window. `from` / `to` are required by
 * the backend and inclusive, expressed as `YYYY-MM-DD`. `granularity` defaults
 * to `day` when omitted.
 */
export async function getAnalyticsOverTime(params: {
  from: string
  to: string
  granularity?: AnalyticsOverTime["granularity"]
}): Promise<AnalyticsOverTime> {
  const query = new URLSearchParams({
    from: params.from,
    to: params.to,
    granularity: params.granularity ?? "day",
  })
  return apiFetch<AnalyticsOverTime>(`/analytics/over-time?${query.toString()}`)
}
