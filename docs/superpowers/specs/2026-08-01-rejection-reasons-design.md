# F3 Rejection Reasons Design Spec

> **Goal:** Enable structured capture and display of rejection reasons when
> applications are rejected — both during pipeline stage moves and after the
> fact from the application workspace.

## Current State (verified against codebase)

**What already exists:**
- ✅ `applications` table has `rejection_reason` (text) + `rejection_reason_category`
  (native enum: visa_sponsorship, lack_of_experience, salary, culture_fit,
  position_filled, no_feedback, other)
- ✅ Timeline events `create_event` service syncs category to `applications`
  table when a REJECTED event is created (but does NOT persist the category on
  the event itself — the repository excludes it)
- ✅ `TimelineEventCreate` schema accepts `rejection_reason_category` and
  validates it is only set for REJECTED events
- ✅ Pipeline move endpoint (`POST /applications/{id}/move`) exists but only
  records stage history — it does NOT touch rejection fields or create timeline
  events
- ✅ Frontend `StageMoveSelect` and `KanbanBoard` drag-and-drop call
  `moveApplication` directly with no dialog/modal

**Gaps to fill:**
1. No way to capture rejection reason during a pipeline move to Rejected
2. No way to edit rejection reasons after the fact from the workspace
3. No rejection reason display in the timeline or workspace
4. The category is accepted on timeline event create but never read back
   (`TimelineEventRead` omits it, and it isn't persisted on the row)

## Architecture Decision: Single Source of Truth

**The `applications` table is the source of truth for rejection data.**

Rationale:
- The columns already exist and are indexed for analytics
- Analytics queries already target `applications.rejection_reason_category`
- Adding a redundant column to `timeline_events` creates two sources of truth
  and bidirectional sync complexity
- The timeline displays rejection info by reading from the application, not
  by parsing event payloads

**Consequence:** The timeline event create flow's existing category sync
(storing on `applications`) stays as-is. We do NOT add
`rejection_reason_category` to the `TimelineEvent` model. The category lives
on the application; the timeline event carries only its `summary`/`note` text.

## Components

### Backend

**1. Extend the pipeline move endpoint to capture rejection data**

`MoveStageRequest` schema gains two optional fields:
- `rejection_reason_category: str | None = None`
- `rejection_reason: str | None = None` (free text, max 255 chars)

`move_application` service: when the target stage's name (case-insensitive,
trimmed) is "rejected", and either field is provided, write them onto the
application row. When moving AWAY from a rejected stage, the fields remain
(an application can be rejected then reopened — we don't auto-clear; clearing
is explicit via the workspace edit).

**2. Allow editing rejection fields via application update**

`ApplicationUpdate` schema already exists. Add `rejection_reason` and
`rejection_reason_category` as optional updatable fields if not already
present (verify in implementation). The `update_application` service applies
them. This powers the workspace edit flow.

**3. No new tables, no migration**

All columns already exist. This is pure service/schema/UI work.

### Frontend

**1. Rejection capture on pipeline move (when target is "Rejected")**

The current move UX is a `<Select>` dropdown (workspace) and drag-and-drop
(Kanban). We add a **rejection dialog** that appears when the target stage is
"Rejected" (matched by stage name, case-insensitive):

- `StageMoveSelect` (workspace): intercept the change; if target is Rejected,
  open a dialog before calling `moveApplication`. Dialog contains:
  - Category `<Select>` (optional, with "No reason" placeholder)
  - Free-text `<Textarea>` for reason (optional)
  - "Move to Rejected" / "Skip" buttons
- `KanbanBoard` drag-and-drop: on drop into a Rejected column, open the same
  dialog before finalising the move. The optimistic update is reverted if the
  user cancels.

The `moveApplication` server action gains optional
`rejection_reason_category` and `rejection_reason` params, forwarded to the
backend move endpoint.

**2. Rejection details section in application workspace**

A new component `<RejectionDetails>` shown only when
`application.rejection_reason_category` is non-null (or
`application.status === "rejected"`). Displays:
- Category badge (color-coded)
- Free-text reason (if present)
- "Edit" affordance opening an inline form (category select + textarea) that
  calls `updateApplication` and revalidates the workspace

**3. Timeline display of rejection**

The `buildTimeline()` merge already handles stage history and timeline
events. We enhance the stage-history entry rendering: when a history entry's
`to_stage.name` is "Rejected", and the application has a rejection category,
append a category badge + reason text below the entry. This reads from the
`application` object passed into the timeline (single source of truth), not
from the event row.

## Data Flow

### Pipeline move to Rejected
```
User drops/selects Rejected
  → Rejection dialog opens
  → User picks category (optional) + reason (optional)
  → moveApplication(applicationId, stageId, { category, reason })
  → POST /applications/{id}/move { to_stage_id, rejection_reason_category, rejection_reason }
  → backend: app_repo.move(...) records stage history
  → backend: if target stage is "rejected", write rejection fields on application
  → revalidate /pipeline, /applications/[id]
```

### Workspace edit of rejection
```
User clicks "Edit" in RejectionDetails
  → Inline form (category select + textarea)
  → updateApplication(applicationId, { rejection_reason_category, rejection_reason })
  → PATCH /applications/{id} { rejection_reason_category, rejection_reason }
  → revalidate /applications/[id]
```

### Timeline display
```
buildTimeline(application, history, ...)
  → for each history entry where to_stage.name === "Rejected":
      attach application.rejection_reason_category as a badge
      attach application.rejection_reason as body text
```

## Edge Cases

- **Moving away from Rejected:** rejection fields persist. This is correct —
  the application was rejected at some point; the user can clear them
  explicitly via the workspace edit if desired.
- **Multiple REJECTED timeline events:** the application's rejection fields
  reflect the most recent write (last-write-wins). Acceptable for v1.
- **Stage named differently (e.g. "Declined"):** the "is this a rejection?"
  check matches `stage.name.lower().strip() == "rejected"`. Documented so
  custom-named rejection stages won't trigger the dialog (acceptable trade-off
  for v1; can be made configurable later).
- **Empty rejection (no category, no text):** allowed — the move still
  proceeds, rejection fields simply aren't written.

## Success Criteria

- ✅ Moving an application to "Rejected" via Kanban drag opens a rejection
  dialog with optional category + reason capture
- ✅ Moving via the workspace `<Select>` opens the same dialog
- ✅ The rejection category and reason persist on the application and survive
  reload
- ✅ The workspace shows a RejectionDetails section for rejected applications
- ✅ RejectionDetails is editable inline
- ✅ Timeline shows the rejection category badge + reason on the Rejected
  stage-transition entry
- ✅ No new database columns or migrations required
- ✅ No regression: existing timeline event rejection sync still works
- ✅ All existing tests pass; new tests cover the move-with-rejection flow

## Testing Strategy

**Backend:**
- `move_application` writes rejection fields when target is "Rejected"
- `move_application` ignores rejection fields when target is not "Rejected"
- `update_application` can set and clear rejection fields
- Existing timeline event rejection sync still works (no regression)

**Frontend:**
- Rejection dialog appears when moving to a "Rejected" stage
- Dialog does NOT appear for non-rejected stages
- `moveApplication` server action forwards rejection fields
- RejectionDetails renders when category is set
- RejectionDetails edit calls `updateApplication`

## Out of Scope (deferred)

- Analytics breakdown of rejection reasons (Phase A in roadmap)
- Custom user-defined rejection categories
- Configurable "rejection stage" detection (beyond name == "rejected")
- Auto-clearing rejection fields when moving away from Rejected

---

**Status:** Corrected and ready for implementation planning