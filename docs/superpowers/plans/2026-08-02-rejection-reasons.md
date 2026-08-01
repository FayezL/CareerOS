# F3 Rejection Reasons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users capture an optional rejection reason (category + free text) when moving an application to the "Rejected" pipeline stage, edit it later from the workspace, and see it surfaced in the timeline.

**Architecture:** The `applications` table is the single source of truth — it already has `rejection_reason` (text) and `rejection_reason_category` (native enum). We extend the existing pipeline move endpoint and application update endpoint to write those fields, and add frontend UI (a rejection dialog on move + a rejection details section in the workspace). No new tables, no migration.

**Tech Stack:** FastAPI + Pydantic + SQLAlchemy (backend), Next.js 15 + React 19 + shadcn/ui + Server Actions (frontend).

---

## File Structure

**Backend (modify only):**
- `backend/src/careeros_api/schemas/pipeline.py` — add rejection fields to `MoveStageRequest`
- `backend/src/careeros_api/schemas/application.py` — add rejection fields to `ApplicationUpdate`
- `backend/src/careeros_api/services/application.py` — wire rejection capture into `move_application` and `update_application`
- `backend/tests/test_pipeline.py` — add rejection-on-move tests
- `backend/tests/test_applications.py` — add rejection-update test

**Frontend (modify + create):**
- `frontend/src/types/index.ts` — add `rejection_reason*` to `Application`, add `RejectionReasonCategory` type
- `frontend/src/features/pipeline/actions.ts` — extend `moveApplication` signature
- `frontend/src/features/pipeline/stage-move-select.tsx` — open rejection dialog before moving to Rejected
- `frontend/src/features/pipeline/rejection-dialog.tsx` — **NEW** shared dialog
- `frontend/src/features/pipeline/kanban-board.tsx` — open rejection dialog on drop into Rejected column
- `frontend/src/features/applications/rejection-details.tsx` — **NEW** workspace section
- `frontend/src/features/workspace/lib/timeline.ts` — surface rejection on Rejected stage entries
- `frontend/src/app/(app)/applications/[id]/page.tsx` — render `<RejectionDetails>`

---

## Task 1: Backend — Extend MoveStageRequest with rejection fields

**Files:**
- Modify: `backend/src/careeros_api/schemas/pipeline.py`

- [ ] **Step 1: Add rejection fields to MoveStageRequest**

Open `backend/src/careeros_api/schemas/pipeline.py` and replace the `MoveStageRequest` class (lines 45–49):

```python
class MoveStageRequest(BaseModel):
    """Move an application to a different stage, optionally annotating the move.

    When the target stage is a rejection stage (name ``"Rejected"``), the
    caller may supply a structured reason that the service writes onto the
    application row for analytics and timeline display.
    """

    to_stage_id: uuid.UUID
    note: str | None = None
    rejection_reason_category: str | None = None
    rejection_reason: str | None = Field(default=None, max_length=255)
```

The `Field` import is already present (line 8).

- [ ] **Step 2: Verify it imports**

Run:
```bash
cd backend
uv run python -c "from careeros_api.schemas.pipeline import MoveStageRequest; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/src/careeros_api/schemas/pipeline.py
git commit -m "feat(api): accept rejection fields on MoveStageRequest"
```

---

## Task 2: Backend — Wire rejection capture into move_application service

**Files:**
- Modify: `backend/src/careeros_api/services/application.py`

- [ ] **Step 1: Update move_application to write rejection fields**

Open `backend/src/careeros_api/services/application.py`. The `move_application` function is at lines 132–150. Replace it with:

```python
async def move_application(
    session: AsyncSession,
    user: User,
    application_id: uuid.UUID,
    data: MoveStageRequest,
) -> ApplicationRead:
    """Move an application to a different stage, recording the transition.

    When the target stage's name is ``"Rejected"`` (case-insensitive) and the
    caller supplied rejection fields, they are written onto the application so
    analytics and the workspace timeline can surface them.
    """
    app_repo = ApplicationRepository(session)
    application = await app_repo.get(user.id, application_id)
    if application is None:
        raise NotFoundError(f"Application {application_id} not found")

    stage_repo = PipelineStageRepository(session)
    target_stage = await stage_repo.get(user.id, data.to_stage_id)
    if target_stage is None:
        raise NotFoundError(f"Pipeline stage {data.to_stage_id} not found")

    moved = await app_repo.move(application, data.to_stage_id, data.note)

    if target_stage.name.strip().lower() == "rejected":
        if data.rejection_reason_category is not None:
            moved.rejection_reason_category = data.rejection_reason_category
        if data.rejection_reason is not None:
            moved.rejection_reason = data.rejection_reason
        await session.flush()

    await session.refresh(moved, attribute_names=["company", "current_stage"])
    return ApplicationRead.model_validate(moved)
```

- [ ] **Step 2: Verify it imports**

Run:
```bash
cd backend
uv run python -c "from careeros_api.services.application import move_application; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/src/careeros_api/services/application.py
git commit -m "feat(api): capture rejection reason on move to Rejected stage"
```

---

## Task 3: Backend — Allow editing rejection fields via ApplicationUpdate

**Files:**
- Modify: `backend/src/careeros_api/schemas/application.py`

- [ ] **Step 1: Add rejection fields to ApplicationUpdate**

Open `backend/src/careeros_api/schemas/application.py`. The `ApplicationUpdate` class is at lines 57–73. Add two fields before the `tags` field (after line 70, the `applied_at` line):

```python
    applied_at: date | None = None
    # Rejection capture — editable from the workspace after a move. Setting
    # either to ``None`` clears it (use ``exclude_unset=True`` semantics).
    rejection_reason: str | None = Field(default=None, max_length=255)
    rejection_reason_category: str | None = None
    # When present (even if empty), the application's tags are replaced with the
    # resolved set. Omit the field to leave tags untouched.
    tags: list[str] | None = None
```

The `Field` import is already present (line 9).

- [ ] **Step 2: Verify it imports**

Run:
```bash
cd backend
uv run python -c "from careeros_api.schemas.application import ApplicationUpdate; print(ApplicationUpdate.model_fields.keys())"
```

Expected output includes `rejection_reason` and `rejection_reason_category`.

- [ ] **Step 3: Verify the repository already handles it**

The `ApplicationRepository.update` method at `backend/src/careeros_api/repositories/application.py:104` uses `exclude_unset=True` and `setattr` loops — it will automatically pick up the new fields because they're real columns on the model. No repository change needed. Verify by checking the model has these columns:

Run:
```bash
cd backend
uv run python -c "from careeros_api.models.application import Application; print('rejection_reason' in Application.__table__.columns, 'rejection_reason_category' in Application.__table__.columns)"
```

Expected: `True True`

- [ ] **Step 4: Commit**

```bash
git add backend/src/careeros_api/schemas/application.py
git commit -m "feat(api): allow editing rejection fields via ApplicationUpdate"
```

---

## Task 4: Backend — Tests for rejection capture on move

**Files:**
- Modify: `backend/tests/test_pipeline.py`

- [ ] **Step 1: Add a helper to find a stage by name**

Open `backend/tests/test_pipeline.py`. After the existing `_create_application` helper (around line 29), add:

```python
def _stage_id(stages: list[dict[str, object]], name: str) -> str:
    """Return the id of the stage whose name matches (case-insensitive)."""
    for s in stages:
        if str(s["name"]).lower() == name.lower():
            return str(s["id"])
    raise AssertionError(f"No stage named {name!r} in {[s['name'] for s in stages]}")
```

- [ ] **Step 2: Write the test**

At the end of the file (after `test_pipeline_isolation`), add:

```python
async def test_move_to_rejected_captures_reason(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _create_company(client, headers, "Reject Co")
    application_id = await _create_application(client, headers, company_id)
    stages = await _stages(client, headers)
    rejected_id = _stage_id(stages, "Rejected")

    move = await client.post(
        f"/api/v1/applications/{application_id}/move",
        headers=headers,
        json={
            "to_stage_id": rejected_id,
            "rejection_reason_category": "salary",
            "rejection_reason": "Offer was 30% below market",
        },
    )
    assert move.status_code == 200, move.text
    moved = move.json()
    assert moved["rejection_reason_category"] == "salary"
    assert moved["rejection_reason"] == "Offer was 30% below market"


async def test_move_to_non_rejected_ignores_rejection_fields(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _create_company(client, headers, "Ignore Co")
    application_id = await _create_application(client, headers, company_id)
    stages = await _stages(client, headers)
    interview_id = _stage_id(stages, "Interview")

    move = await client.post(
        f"/api/v1/applications/{application_id}/move",
        headers=headers,
        json={
            "to_stage_id": interview_id,
            "rejection_reason_category": "salary",
            "rejection_reason": "should be ignored",
        },
    )
    assert move.status_code == 200, move.text
    moved = move.json()
    assert moved["rejection_reason_category"] is None
    assert moved["rejection_reason"] is None


async def test_move_to_rejected_without_reason_succeeds(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _create_company(client, headers, "Silent Co")
    application_id = await _create_application(client, headers, company_id)
    stages = await _stages(client, headers)
    rejected_id = _stage_id(stages, "Rejected")

    move = await client.post(
        f"/api/v1/applications/{application_id}/move",
        headers=headers,
        json={"to_stage_id": rejected_id},
    )
    assert move.status_code == 200, move.text
    moved = move.json()
    assert moved["rejection_reason_category"] is None
    assert moved["rejection_reason"] is None
```

- [ ] **Step 3: Run the tests to verify they pass**

Run:
```bash
cd backend
uv run --extra dev pytest tests/test_pipeline.py -v -k "rejected"
```

Expected: 3 passed.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_pipeline.py
git commit -m "test(api): rejection capture on move to Rejected stage"
```

---

## Task 5: Backend — Test for editing rejection fields via update

**Files:**
- Modify: `backend/tests/test_applications.py`

- [ ] **Step 1: Read the existing test file to find the patterns**

Run:
```bash
cd backend
head -40 tests/test_applications.py
```

Note the imports (`AsyncClient`, `AuthHeaders`) and the helper patterns used.

- [ ] **Step 2: Add the test**

At the end of `backend/tests/test_applications.py`, add:

```python
async def test_update_rejection_fields(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    # Create a company + application via the API.
    company = await client.post(
        "/api/v1/companies", headers=headers, json={"name": "Update Reject Co"}
    )
    assert company.status_code == 201, company.text
    company_id = company.json()["id"]
    app_resp = await client.post(
        "/api/v1/applications",
        headers=headers,
        json={"company_id": company_id, "role_title": "Eng"},
    )
    assert app_resp.status_code == 201, app_resp.text
    application_id = app_resp.json()["id"]

    # Set rejection fields via PATCH.
    patch = await client.patch(
        f"/api/v1/applications/{application_id}",
        headers=headers,
        json={
            "rejection_reason_category": "culture_fit",
            "rejection_reason": "Team didn't feel like a match",
        },
    )
    assert patch.status_code == 200, patch.text
    updated = patch.json()
    assert updated["rejection_reason_category"] == "culture_fit"
    assert updated["rejection_reason"] == "Team didn't feel like a match"

    # Clear the category via PATCH (set to null).
    clear = await client.patch(
        f"/api/v1/applications/{application_id}",
        headers=headers,
        json={"rejection_reason_category": None},
    )
    assert clear.status_code == 200, clear.text
    assert clear.json()["rejection_reason_category"] is None
```

- [ ] **Step 3: Run the test**

Run:
```bash
cd backend
uv run --extra dev pytest tests/test_applications.py -v -k "rejection"
```

Expected: 1 passed.

- [ ] **Step 4: Run the full backend suite to confirm no regressions**

Run:
```bash
cd backend
uv run --extra dev pytest -q
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_applications.py
git commit -m "test(api): edit rejection fields via ApplicationUpdate"
```

---

## Task 6: Frontend — Types and shared constants

**Files:**
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: Add RejectionReasonCategory type and extend Application**

Open `frontend/src/types/index.ts`. After the `TimelineImportance` type (around line 32), add:

```typescript
/** Structured reason an application was rejected. */
export type RejectionReasonCategory =
  | "visa_sponsorship"
  | "lack_of_experience"
  | "salary"
  | "culture_fit"
  | "position_filled"
  | "no_feedback"
  | "other"
```

Then, in the `Application` interface (around lines 113–135), add the two rejection fields after `applied_at`:

```typescript
  applied_at: string | null
  rejection_reason: string | null
  rejection_reason_category: RejectionReasonCategory | null
  job_description: string | null
```

- [ ] **Step 2: Verify typecheck**

Run:
```bash
cd frontend
pnpm typecheck
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/index.ts
git commit -m "feat(frontend): add RejectionReasonCategory type and Application fields"
```

---

## Task 7: Frontend — Create the shared RejectionDialog component

**Files:**
- Create: `frontend/src/features/pipeline/rejection-dialog.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/src/features/pipeline/rejection-dialog.tsx`:

```tsx
"use client"

import { useState } from "react"
import { toast } from "sonner"

import type { RejectionReasonCategory } from "@/types"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"

import { moveApplication } from "./actions"

const REJECTION_CATEGORIES: { value: RejectionReasonCategory; label: string }[] = [
  { value: "visa_sponsorship", label: "Visa sponsorship" },
  { value: "lack_of_experience", label: "Lack of experience" },
  { value: "salary", label: "Salary" },
  { value: "culture_fit", label: "Culture fit" },
  { value: "position_filled", label: "Position filled" },
  { value: "no_feedback", label: "No feedback" },
  { value: "other", label: "Other" },
]

type RejectionDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  applicationId: string
  toStageId: string
  onSuccess?: () => void
}

export function RejectionDialog({
  open,
  onOpenChange,
  applicationId,
  toStageId,
  onSuccess,
}: RejectionDialogProps) {
  const [category, setCategory] = useState<RejectionReasonCategory | "">("")
  const [reason, setReason] = useState("")
  const [isPending, startTransition] = useState(false)

  async function handleConfirm() {
    startTransition(true)
    const payload: Record<string, unknown> = { to_stage_id: toStageId }
    if (category) payload.rejection_reason_category = category
    if (reason.trim()) payload.rejection_reason = reason.trim()

    const result = await moveApplication(applicationId, toStageId, {
      rejection_reason_category: category || undefined,
      rejection_reason: reason.trim() || undefined,
    })

    startTransition(false)
    if (result.ok) {
      toast.success("Moved to Rejected")
      onOpenChange(false)
      onSuccess?.()
    } else {
      toast.error(result.error ?? "Failed to move application")
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Move to Rejected</AlertDialogTitle>
          <AlertDialogDescription>
            Optionally capture why this application was rejected. You can change this later.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label htmlFor="rejection-category">Reason category</Label>
            <Select value={category} onValueChange={(v) => setCategory(v as RejectionReasonCategory)}>
              <SelectTrigger id="rejection-category" className="w-full">
                <SelectValue placeholder="Select a reason (optional)" />
              </SelectTrigger>
              <SelectContent>
                {REJECTION_CATEGORIES.map((c) => (
                  <SelectItem key={c.value} value={c.value}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="rejection-text">Details (optional)</Label>
            <Textarea
              id="rejection-text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Salary was 30% below market"
              rows={3}
              maxLength={255}
            />
          </div>
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            disabled={isPending}
            onClick={(e) => {
              e.preventDefault()
              handleConfirm()
            }}
          >
            {isPending ? "Moving…" : "Move to Rejected"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

export { REJECTION_CATEGORIES }
```

- [ ] **Step 2: Verify lint + typecheck**

Run:
```bash
cd frontend
pnpm lint
pnpm typecheck
```

Expected: clean. (If `Textarea` or `Label` components don't exist yet, run `pnpm dlx shadcn@latest add textarea label` first.)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/pipeline/rejection-dialog.tsx
git commit -m "feat(pipeline): shared RejectionDialog component"
```

---

## Task 8: Frontend — Extend moveApplication server action

**Files:**
- Modify: `frontend/src/features/pipeline/actions.ts`

- [ ] **Step 1: Update moveApplication signature and body**

Open `frontend/src/features/pipeline/actions.ts`. Replace the `moveApplication` function (lines 92–109):

```typescript
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
```

- [ ] **Step 2: Verify typecheck**

Run:
```bash
cd frontend
pnpm typecheck
```

Expected: clean.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/pipeline/actions.ts
git commit -m "feat(pipeline): accept rejection fields in moveApplication action"
```

---

## Task 9: Frontend — Wire RejectionDialog into StageMoveSelect

**Files:**
- Modify: `frontend/src/features/pipeline/stage-move-select.tsx`

- [ ] **Step 1: Add dialog state and stage-name check**

Open `frontend/src/features/pipeline/stage-move-select.tsx`. Replace the entire file:

```tsx
"use client"

import { useState } from "react"
import { toast } from "sonner"

import type { PipelineStage } from "@/types"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import { moveApplication } from "./actions"
import { RejectionDialog } from "./rejection-dialog"

type StageMoveSelectProps = {
  applicationId: string
  stages: PipelineStage[]
  currentStageId: string | null | undefined
}

/** Select control that moves an application between pipeline stages. */
export function StageMoveSelect({ applicationId, stages, currentStageId }: StageMoveSelectProps) {
  const [isPending, setIsPending] = useState(false)
  const [pendingRejection, setPendingRejection] = useState<PipelineStage | null>(null)

  function isRejectedStage(stage: PipelineStage): boolean {
    return stage.name.trim().toLowerCase() === "rejected"
  }

  async function handleChange(toStageId: string) {
    if (toStageId === currentStageId) return
    const target = stages.find((s) => s.id === toStageId)
    if (target && isRejectedStage(target)) {
      setPendingRejection(target)
      return
    }
    await executeMove(toStageId)
  }

  async function executeMove(
    toStageId: string,
    options?: { rejection_reason_category?: string; rejection_reason?: string },
  ) {
    setIsPending(true)
    const result = await moveApplication(applicationId, toStageId, options)
    setIsPending(false)
    if (result.ok) {
      toast.success("Application moved")
    } else {
      toast.error(result.error ?? "Failed to move application")
    }
  }

  if (stages.length === 0) {
    return (
      <Select disabled>
        <SelectTrigger className="w-[220px]">
          <SelectValue placeholder="No stages" />
        </SelectTrigger>
      </Select>
    )
  }

  return (
    <>
      <Select
        defaultValue={currentStageId ?? undefined}
        onValueChange={handleChange}
        disabled={isPending}
      >
        <SelectTrigger className="w-[220px]">
          <SelectValue placeholder="Select a stage" />
        </SelectTrigger>
        <SelectContent>
          {stages.map((stage) => (
            <SelectItem key={stage.id} value={stage.id}>
              <span className="flex items-center gap-2">
                <span
                  aria-hidden
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: stage.color ?? "#94a3b8" }}
                />
                {stage.name}
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {pendingRejection && (
        <RejectionDialog
          open={true}
          onOpenChange={(open) => {
            if (!open) setPendingRejection(null)
          }}
          applicationId={applicationId}
          toStageId={pendingRejection.id}
        />
      )}
    </>
  )
}
```

- [ ] **Step 2: Verify lint + typecheck**

Run:
```bash
cd frontend
pnpm lint
pnpm typecheck
```

Expected: clean.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/pipeline/stage-move-select.tsx
git commit -m "feat(pipeline): open RejectionDialog when moving to Rejected stage"
```

---

## Task 10: Frontend — Wire RejectionDialog into KanbanBoard drag-and-drop

**Files:**
- Modify: `frontend/src/features/pipeline/kanban-board.tsx`

- [ ] **Step 1: Read the current handleDrop logic**

Open `frontend/src/features/pipeline/kanban-board.tsx`. Find the `handleDragEnd` / `onDragEnd` handler (around lines 88–106). It currently calls `moveApplication(applicationId, toStageId)` optimistically.

- [ ] **Step 2: Add rejection dialog state and intercept drops into Rejected**

At the top of the `Board` component function (around line 57), add state:

```typescript
const [pendingRejection, setPendingRejection] = useState<{
  applicationId: string
  stage: PipelineStage
} | null>(null)
```

Add `useState` to the React import at the top of the file if not already present.

In the `handleDragEnd` (or equivalent) handler, before the optimistic move, check if the target stage is "Rejected":

```typescript
const targetStage = stages.find((s) => s.id === toStageId)
if (targetStage && targetStage.name.trim().toLowerCase() === "rejected") {
  // Revert optimistic update — dialog will handle the move
  setApps((prev) =>
    prev.map((a) => (a.id === applicationId ? { ...a, stage_id: fromStageId } : a)),
  )
  setPendingRejection({ applicationId, stage: targetStage })
  return
}
```

Add the dialog render at the bottom of the component's JSX (before the closing fragment):

```tsx
{pendingRejection && (
  <RejectionDialog
    open={true}
    onOpenChange={(open) => {
      if (!open) setPendingRejection(null)
    }}
    applicationId={pendingRejection.applicationId}
    toStageId={pendingRejection.stage.id}
    onSuccess={() => {
      // Apply the move optimistically after dialog success
      setApps((prev) =>
        prev.map((a) =>
          a.id === pendingRejection.applicationId
            ? { ...a, stage_id: pendingRejection.stage.id }
            : a,
        ),
      )
      setPendingRejection(null)
    }}
  />
)}
```

Add the import at the top:
```typescript
import { RejectionDialog } from "./rejection-dialog"
```

- [ ] **Step 3: Verify lint + typecheck**

Run:
```bash
cd frontend
pnpm lint
pnpm typecheck
```

Expected: clean.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/pipeline/kanban-board.tsx
git commit -m "feat(pipeline): open RejectionDialog on drop into Rejected column"
```

---

## Task 11: Frontend — Create RejectionDetails workspace section

**Files:**
- Create: `frontend/src/features/applications/rejection-details.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/src/features/applications/rejection-details.tsx`:

```tsx
"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { Pencil } from "lucide-react"

import type { Application, RejectionReasonCategory } from "@/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { REJECTION_CATEGORIES } from "@/features/pipeline/rejection-dialog"
import { updateApplication } from "@/features/applications/actions"

const CATEGORY_LABELS: Record<RejectionReasonCategory, string> = {
  visa_sponsorship: "Visa sponsorship",
  lack_of_experience: "Lack of experience",
  salary: "Salary",
  culture_fit: "Culture fit",
  position_filled: "Position filled",
  no_feedback: "No feedback",
  other: "Other",
}

const CATEGORY_COLORS: Record<RejectionReasonCategory, string> = {
  visa_sponsorship: "bg-blue-100 text-blue-800",
  lack_of_experience: "bg-amber-100 text-amber-800",
  salary: "bg-red-100 text-red-800",
  culture_fit: "bg-purple-100 text-purple-800",
  position_filled: "bg-slate-100 text-slate-800",
  no_feedback: "bg-slate-100 text-slate-800",
  other: "bg-slate-100 text-slate-800",
}

type RejectionDetailsProps = {
  application: Application
}

export function RejectionDetails({ application }: RejectionDetailsProps) {
  const router = useRouter()
  const [isEditing, setIsEditing] = useState(false)
  const [category, setCategory] = useState<RejectionReasonCategory | "">(
    (application.rejection_reason_category as RejectionReasonCategory) ?? "",
  )
  const [reason, setReason] = useState(application.rejection_reason ?? "")
  const [isPending, startTransition] = useState(false)

  if (
    !application.rejection_reason_category &&
    !application.rejection_reason &&
    application.status !== "rejected"
  ) {
    return null
  }

  async function handleSave() {
    startTransition(true)
    const result = await updateApplication(application.id, {
      rejection_reason_category: category || null,
      rejection_reason: reason.trim() || null,
    })
    startTransition(false)

    if (result?.ok === false) {
      toast.error(result.error ?? "Failed to update rejection reason")
      return
    }
    toast.success("Rejection reason updated")
    setIsEditing(false)
    router.refresh()
  }

  return (
    <section className="rounded-lg border border-border bg-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          Rejection
        </h3>
        {!isEditing && (
          <Button variant="ghost" size="sm" onClick={() => setIsEditing(true)}>
            <Pencil className="mr-1.5 h-3.5 w-3.5" />
            Edit
          </Button>
        )}
      </div>

      {isEditing ? (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="edit-rejection-category">Reason category</Label>
            <Select
              value={category}
              onValueChange={(v) => setCategory(v as RejectionReasonCategory)}
            >
              <SelectTrigger id="edit-rejection-category" className="w-full">
                <SelectValue placeholder="Select a reason (optional)" />
              </SelectTrigger>
              <SelectContent>
                {REJECTION_CATEGORIES.map((c) => (
                  <SelectItem key={c.value} value={c.value}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="edit-rejection-text">Details</Label>
            <Textarea
              id="edit-rejection-text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Salary was 30% below market"
              rows={3}
              maxLength={255}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setIsEditing(false)}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleSave} disabled={isPending}>
              {isPending ? "Saving…" : "Save"}
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          {application.rejection_reason_category ? (
            <Badge
              className={
                CATEGORY_COLORS[application.rejection_reason_category] ??
                "bg-slate-100 text-slate-800"
              }
            >
              {CATEGORY_LABELS[application.rejection_reason_category] ??
                application.rejection_reason_category}
            </Badge>
          ) : (
            <p className="text-sm text-muted-foreground">No category captured.</p>
          )}
          {application.rejection_reason && (
            <p className="text-sm text-foreground">{application.rejection_reason}</p>
          )}
        </div>
      )}
    </section>
  )
}
```

- [ ] **Step 2: Check updateApplication action signature**

Open `frontend/src/features/applications/actions.ts` and verify the `updateApplication` action accepts a second argument with optional fields. If it only accepts `FormData`, add an overload that accepts a plain object. (Read the file first to match the existing pattern.)

- [ ] **Step 3: Verify lint + typecheck**

Run:
```bash
cd frontend
pnpm lint
pnpm typecheck
```

Expected: clean.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/applications/rejection-details.tsx
git commit -m "feat(applications): RejectionDetails workspace section with inline edit"
```

---

## Task 12: Frontend — Render RejectionDetails in the workspace page

**Files:**
- Modify: `frontend/src/app/(app)/applications/[id]/page.tsx`

- [ ] **Step 1: Add the import and render the component**

Open `frontend/src/app/(app)/applications/[id]/page.tsx`. Add the import near the other feature imports (after line 18):

```typescript
import { RejectionDetails } from "@/features/applications/rejection-details"
```

In the right-column `<div className="space-y-8">` (around line 171–176), add `<RejectionDetails>` between `ApplicationDetails` and the documents panel:

```tsx
        <div className="space-y-8">
          <ApplicationDetails application={application} />
          <RejectionDetails application={application} />
          <div className="border-t border-border pt-6">
            <DocumentsPanel applicationId={application.id} initial={documents} />
          </div>
        </div>
```

- [ ] **Step 2: Verify lint + typecheck**

Run:
```bash
cd frontend
pnpm lint
pnpm typecheck
```

Expected: clean.

- [ ] **Step 3: Commit**

```bash
git add "frontend/src/app/(app)/applications/[id]/page.tsx"
git commit -m "feat(workspace): render RejectionDetails section"
```

---

## Task 13: Frontend — Surface rejection on timeline stage entries

**Files:**
- Modify: `frontend/src/features/workspace/lib/timeline.ts`

- [ ] **Step 1: Extend TimelineItem to carry optional rejection data**

Open `frontend/src/features/workspace/lib/timeline.ts`. Add fields to the `TimelineItem` interface (after line 30, `borderColor`):

```typescript
  rejectionCategory?: string | null
  rejectionReason?: string | null
```

- [ ] **Step 2: Populate rejection data on stage entries**

In the `buildTimeline` function's stage-history loop (around lines 139–155), after setting `borderColor`, add:

```typescript
      borderColor: "border-l-blue-500",
      rejectionCategory:
        stage.to_stage.name.trim().toLowerCase() === "rejected"
          ? application.rejection_reason_category
          : null,
      rejectionReason:
        stage.to_stage.name.trim().toLowerCase() === "rejected"
          ? application.rejection_reason
          : null,
```

- [ ] **Step 3: Render rejection in ApplicationTimeline**

Open `frontend/src/features/applications/application-timeline.tsx`. In the render of each timeline item (inside the `<li>` block, after the `body` render around lines 88–92), add:

```tsx
                {item.rejectionCategory && (
                  <span className="mt-1 inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
                    {item.rejectionCategory}
                  </span>
                )}
```

- [ ] **Step 4: Verify lint + typecheck**

Run:
```bash
cd frontend
pnpm lint
pnpm typecheck
```

Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/workspace/lib/timeline.ts frontend/src/features/applications/application-timeline.tsx
git commit -m "feat(timeline): surface rejection category on Rejected stage entries"
```

---

## Task 14: Full verification

- [ ] **Step 1: Backend full check**

Run:
```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run --extra dev pytest -q
```

Expected: all clean, all tests pass.

- [ ] **Step 2: Frontend full check**

Run:
```bash
cd frontend
pnpm lint
pnpm typecheck
pnpm build
```

Expected: all clean, build succeeds.

- [ ] **Step 3: Fix any issues found, then commit**

If any issues were found and fixed, commit them. Otherwise, no commit needed.

---

## Self-Review Checklist

**Spec coverage:**
- [x] Move to Rejected captures category + reason — Task 2, Task 4 (tests)
- [x] Non-Rejected moves ignore rejection fields — Task 4 (test)
- [x] Rejection fields editable via workspace — Task 3, Task 5 (tests), Task 11 (UI)
- [x] Rejection dialog on pipeline move — Task 7 (component), Task 9 (select), Task 10 (kanban)
- [x] RejectionDetails workspace section — Task 11
- [x] Timeline shows rejection on Rejected stage entries — Task 13
- [x] No new migration required — verified (columns exist)
- [x] No regression on timeline event rejection sync — Task 4 (full suite runs)

**Placeholder scan:** No TBD/TODO/placeholder steps. Every step has complete code.

**Type consistency:**
- `RejectionReasonCategory` type matches between `types/index.ts` and `rejection-dialog.tsx`
- `moveApplication` signature consistent across `actions.ts`, `stage-move-select.tsx`, `kanban-board.tsx`, `rejection-dialog.tsx`
- Backend `MoveStageRequest` field names match frontend payload keys