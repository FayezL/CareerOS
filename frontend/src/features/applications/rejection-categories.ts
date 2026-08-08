import type { RejectionReasonCategory } from "@/types"

/**
 * Canonical rejection reason categories and their human-readable labels.
 *
 * Single source of truth for the frontend. The set MUST stay in sync with the
 * backend Pydantic `RejectionReasonCategory` Literal
 * (`backend/src/careeros_api/schemas/pipeline.py`) and the native PG enum
 * (`backend/src/careeros_api/models/application.py`).
 */
export const REJECTION_CATEGORY_OPTIONS: {
  value: RejectionReasonCategory
  label: string
}[] = [
  { value: "visa_sponsorship", label: "Visa sponsorship" },
  { value: "lack_of_experience", label: "Lack of experience" },
  { value: "salary", label: "Salary" },
  { value: "culture_fit", label: "Culture fit" },
  { value: "position_filled", label: "Position filled" },
  { value: "no_feedback", label: "No feedback" },
  { value: "other", label: "Other" },
]

export const REJECTION_CATEGORY_LABELS: Record<RejectionReasonCategory, string> =
  Object.fromEntries(REJECTION_CATEGORY_OPTIONS.map((c) => [c.value, c.label])) as Record<
    RejectionReasonCategory,
    string
  >
