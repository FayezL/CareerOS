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

/** Lightweight company record returned by the autocomplete search endpoint. */
export interface CompanyOption {
  id: string
  name: string
  website: string | null
  industry: string | null
  location: string | null
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
  from_stage: StageRef | null
  to_stage: StageRef
  changed_at: string
  note: string | null
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
  user_id?: string | null
  application_id: string | null
  interview_id: string | null
  contact_id: string | null
  title: string
  due_at: string | null
  completed: boolean
  completed_at: string | null
  created_at: string
  updated_at: string
}

/** Payload for creating a reminder (`title` and `due_at` are required). */
export interface ReminderCreate {
  application_id?: string | null
  interview_id?: string | null
  title: string
  due_at: string
}

/** Partial payload for updating a reminder. */
export interface ReminderUpdate {
  application_id?: string | null
  interview_id?: string | null
  title?: string
  due_at?: string
}

/** Headline totals and rates for the analytics summary endpoint. */
export interface AnalyticsSummary {
  generated_at: string
  totals: {
    applications: number
    active: number
    interviews: number
    offers: number
  }
  response_rate: number
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

/**
 * The current user's subscription.
 *
 * Mirrors the backend `SubscriptionRead` schema exactly.
 */
export interface Subscription {
  id: string
  user_id: string
  plan: PlanTier
  status: SubscriptionStatus
  stripe_customer_id: string | null
  stripe_subscription_id: string | null
  current_period_end: string | null
  created_at: string
  updated_at: string
}

/** Request payload for `POST /billing/checkout`. */
export interface CheckoutRequest {
  plan: PlanTier
  success_url: string
  cancel_url: string
}

/** Checkout session returned by `POST /billing/checkout`. */
export interface CheckoutSession {
  id: string
  url: string
}

/** Request payload for `POST /billing/portal`. */
export interface PortalRequest {
  return_url: string
}

/** Billing-portal session returned by `POST /billing/portal`. */
export interface PortalSession {
  url: string
}

/**
 * AI generation request/response types.
 *
 * These mirror the FastAPI backend's `schemas/ai.py` contracts exactly.
 * The backend returns a `GenerationResponse` whose sole field is `text`.
 */

/** Request payload for `POST /ai/tailor-resume`. */
export interface TailorResumeRequest {
  resume_text: string
  job_description: string
}

/** Request payload for `POST /ai/cover-letter`. */
export interface CoverLetterRequest {
  company: string
  role: string
  resume_text: string
}

/** Request payload for `POST /ai/interview-prep`. */
export interface InterviewPrepRequest {
  role: string
  job_description: string
}

/** The generated text returned by every AI endpoint (`GenerationResponse`). */
export interface GenerationResponse {
  text: string
}

/**
 * Generic paginated envelope.
 *
 * The backend may return either this shape or a bare array for list endpoints;
 * `unwrapList` in `services/api-client.ts` normalizes both to an array.
 */
export interface PageOut<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}
