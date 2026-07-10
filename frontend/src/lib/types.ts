/**
 * Shared API types.
 *
 * These mirror the FastAPI backend's JSON contracts (snake_case). They are
 * intentionally permissive about nullability because every user-owned resource
 * shares the same `id` / `created_at` / `updated_at` envelope, while the
 * mutable fields are optional on input.
 */

/** The lifecycle states an application can be in. */
export type ApplicationStatus = "active" | "archived" | "rejected" | "accepted"

/** A minimal company reference embedded on related resources. */
export interface CompanyRef {
  id: string
  name: string
}

/** A minimal pipeline-stage reference embedded on related resources. */
export interface StageRef {
  id: string
  name: string
}

/** A company the user is tracking or engaging with. */
export interface Company {
  id: string
  name: string
  website: string | null
  industry: string | null
  size: string | null
  location: string | null
  linkedin_url: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

/** A single job application. */
export interface Application {
  id: string
  company_id: string
  /** Embedded company summary, present on read endpoints. */
  company?: CompanyRef | null
  role_title: string
  status: ApplicationStatus
  /** The pipeline stage this application currently sits in. */
  stage_id?: string | null
  /** Embedded stage summary, present on read endpoints. */
  stage?: StageRef | null
  job_url: string | null
  source: string | null
  salary_min: number | null
  salary_max: number | null
  salary_currency: string | null
  applied_at: string | null
  job_description: string | null
  created_at: string
  updated_at: string
}

/** A user-owned pipeline stage (Kanban column). */
export interface PipelineStage {
  id: string
  user_id?: string | null
  name: string
  position: number
  color: string | null
  is_default?: boolean | null
  created_at: string
  updated_at: string
}

/** A single entry in an application's stage-change timeline. */
export interface StageHistory {
  id: string
  application_id: string
  to_stage_id: string
  to_stage: StageRef
  note: string | null
  occurred_at: string
}

/** The type of an interview event. */
export type InterviewType =
  "phone_screen" | "video_call" | "onsite" | "take_home" | "technical" | "final"

/** The role a contact plays in the user's search. */
export type ContactRole = "recruiter" | "hiring_manager" | "interviewer" | "referral" | "other"

/** The category of a stored document. */
export type DocumentType = "resume" | "cover_letter" | "offer_letter" | "other"

/** A person (recruiter, hiring manager, interviewer, referral). */
export interface Contact {
  id: string
  company_id: string | null
  /** Embedded company summary, present on read endpoints. */
  company?: CompanyRef | null
  name: string
  email: string | null
  linkedin_url: string | null
  role: ContactRole | null
  created_at: string
  updated_at: string
}

/** A scheduled interview tied to an application. */
export interface Interview {
  id: string
  application_id: string
  type: InterviewType
  scheduled_at: string
  duration_minutes: number | null
  location: string | null
  interviewer_contact_id: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

/** A free-form note attached to an application and/or contact. */
export interface Note {
  id: string
  application_id: string | null
  contact_id: string | null
  title: string | null
  body: string | null
  created_at: string
  updated_at: string
}

/** A stored document; metadata lives in CareerOS, bytes in object storage. */
export interface Document {
  id: string
  application_id: string | null
  type: DocumentType
  name: string
  mime_type: string | null
  size_bytes: number | null
  storage_uri: string | null
  /** Signed upload URL — present only on the create response. */
  upload_url?: string | null
  /** HTTP method to use when uploading bytes (`PUT`/`POST`). */
  upload_method?: string | null
  /** Headers the client must send with the upload request. */
  upload_headers?: Record<string, string> | null
  /** When the signed upload URL expires. */
  expires_at?: string | null
  created_at: string
  updated_at: string
}

/** A follow-up reminder tied to an application, contact, or interview. */
export interface Reminder {
  id: string
  application_id: string | null
  contact_id: string | null
  title: string
  due_at: string | null
  completed: boolean
  completed_at: string | null
  created_at: string
  updated_at: string
}

/** Headline totals and rates for the analytics summary endpoint. */
export interface AnalyticsSummary {
  generated_at: string
  totals: {
    applications: number
    active: number
    offers: number
    rejections: number
  }
  response_rate: number
  active_companies: number
}

/** A single stage row in the analytics funnel. */
export interface FunnelPoint {
  stage_id: string
  name: string
  position: number
  entered: number
  distinct_applications: number
}

/** The full analytics funnel response. */
export interface AnalyticsFunnel {
  generated_at: string
  stages: FunnelPoint[]
}

/** A single time bucket in the applications-over-time series. */
export interface OverTimePoint {
  bucket: string
  applications: number
}

/** The applications-over-time response. */
export interface AnalyticsOverTime {
  generated_at: string
  granularity: "day" | "week"
  from: string
  to: string
  buckets: OverTimePoint[]
}

/** The subscription plan tiers offered by CareerOS. */
export type PlanTier = "free" | "pro" | "team"

/** Lifecycle state of a subscription. `noop` means billing is disabled. */
export type SubscriptionStatus = "active" | "trialing" | "past_due" | "canceled" | "noop"

/** The current user's subscription, when billing is enabled. */
export interface Subscription {
  plan: PlanTier
  status: SubscriptionStatus
  current_period_end: string | null
  cancel_at_period_end: boolean
}

/** The AI generation tasks surfaced in CareerOS. */
export type AITask = "tailor_resume" | "cover_letter" | "interview_prep"

/** Request payload for tailoring a resume to a job description. */
export interface TailorResumeRequest {
  resume: string
  job_description: string
}

/** Request payload for drafting a cover letter for an application. */
export interface CoverLetterRequest {
  application_id: string
  company_name?: string
  role_title?: string
  job_description?: string
}

/** Request payload for generating interview prep questions for a role. */
export interface InterviewPrepRequest {
  role_title: string
  company_name?: string
  job_description?: string
}

/** A completed AI generation result. */
export interface AIResult {
  task: AITask
  content: string
}

/**
 * Generic paginated envelope.
 *
 * The backend may return either this shape or a bare array for list endpoints;
 * `unwrapList` in `api-client.ts` normalizes both to an array.
 */
export interface PageOut<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}
