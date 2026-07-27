# F2 — Custom Timeline Events (Activity Feed)

> **Status:** Design approved, pending implementation plan.
> **Date:** 2026-07-27.
> **Depends on:** Migration 0009 (table + model exist). Adds migration 0010.
> **Roadmap ref:** `REDESIGN_ROADMAP.md` §F2.

---

## 1. Vision

The application workspace timeline today shows only stage transitions (from
`application_stage_history`) plus a synthetic "Applied" entry. F2 adds
**user-authored activity events** — recruiter messages, phone screens, follow-up
emails, take-homes, notes — so the timeline tells the full story of an
application, not just stage moves.

The schema is designed to **evolve into a general Activity Feed** (system events
like "resume changed", "document uploaded", "reminder completed") without a
future rewrite. The `source` column (§4) is the enabler.

---

## 2. Scope

**In scope (F2):**
- Backend: schema, repository, service, routes for `timeline_events`.
- Migration 0010: convert `event_type` to a native enum; rename `title` →
  `summary`; add `importance`, `follow_up_date`, `source` columns.
- Frontend: `TimelineEvent` type; centralized metadata; merge logic;
  server actions; "Add Event" form; delete-with-confirmation; timeline merge.
- Rejection-reason capture when `event_type = REJECTED` (updates
  `applications.rejection_reason_*`).

**Out of scope (explicitly deferred):**
- Attachments / file uploads on events (§8 — schema-ready, not built).
- Search across timeline events (§9 — documented; not built).
- `follow_up_date` UI (column exists; not surfaced in F2).
- System-generated events (column `source` exists; all F2 events are `user`).

---

## 3. Migration 0010

The `timeline_events` table exists (migration 0009) with `event_type` as
`String(64)` and `title` as `String(255)`. Migration 0010 refines it.

### 0010_timeline_event_enrichment.py

**upgrade():**

1. **Create native enum `timeline_event_type`** with values:
   `APPLIED, EMAIL, CALL, FOLLOW_UP, PHONE_SCREEN, TECHNICAL, SYSTEM_DESIGN,
   ONSITE, TAKE_HOME, RECRUITER_MESSAGE, OFFER, ACCEPTED, REJECTED, NOTE,
   CUSTOM`.

2. **Create native enum `timeline_importance`** with values:
   `NORMAL, IMPORTANT, MILESTONE`.

3. **Alter `event_type` column** from `String(64)` to `timeline_event_type`
   enum. The table has no real data (new, unreleased feature), so a direct
   type change with `postgresql_using` is safe.

4. **Rename `title` → `summary`.**

5. **Add columns:**
   - `importance` — `timeline_importance`, NOT NULL, `server_default='NORMAL'`.
   - `follow_up_date` — `TIMESTAMPTZ`, nullable. (Schema-ready for future
     reminder integration; not surfaced in F2 UI.)
   - `source` — `String(32)`, NOT NULL, `server_default='user'`. Enabler for
     the Activity Feed evolution (§10). All F2 events are `'user'`.

6. **Drop old index** `ix_timeline_events_application_id_occurred_at` and
   recreate it to include `importance` as an include column? **No** — keep the
   existing composite index as-is; `importance` filtering is not a hot path
   in F2.

**downgrade():** reverse all of the above; drop both enum types.

### Conventions followed
- Native enum (not CHECK) — matches codebase pattern
  (`application_status`, `interview_type`, `document_type`,
  `rejection_reason_category`).
- ORM model updated in lockstep with migration (AGENTS.md requirement).
- `server_default` on new NOT NULL columns so existing rows (if any) get a
  value.

---

## 4. Data model

### `models/timeline_event.py` (updated)

```python
import enum

class TimelineEventType(enum.Enum):
    APPLIED = "APPLIED"
    EMAIL = "EMAIL"
    CALL = "CALL"
    FOLLOW_UP = "FOLLOW_UP"
    PHONE_SCREEN = "PHONE_SCREEN"
    TECHNICAL = "TECHNICAL"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"
    ONSITE = "ONSITE"
    TAKE_HOME = "TAKE_HOME"
    RECRUITER_MESSAGE = "RECRUITER_MESSAGE"
    OFFER = "OFFER"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    NOTE = "NOTE"
    CUSTOM = "CUSTOM"

class TimelineImportance(enum.Enum):
    NORMAL = "NORMAL"
    IMPORTANT = "IMPORTANT"
    MILESTONE = "MILESTONE"
```

Column changes on `TimelineEvent`:
- `event_type: Mapped[TimelineEventType]` — `sa.Enum(TimelineEventType, name="timeline_event_type")`.
- `title` → **`summary: Mapped[str | None]`** — renamed.
- `importance: Mapped[TimelineImportance]` — NOT NULL, default `NORMAL`.
- `follow_up_date: Mapped[datetime | None]` — nullable.
- `source: Mapped[str]` — NOT NULL, default `"user"`.

`__table_args__`: existing two indexes unchanged.

---

## 5. Backend API

### 5.1 Schema (`schemas/timeline_event.py`)

```python
class TimelineEventBase(BaseModel):
    application_id: uuid.UUID
    event_type: TimelineEventType
    summary: str | None = Field(default=None, max_length=255)
    note: str | None = None
    occurred_at: datetime | None = None          # None → server now()
    importance: TimelineImportance = TimelineImportance.NORMAL

class TimelineEventCreate(TimelineEventBase):
    rejection_reason_category: RejectionReasonCategory | None = None
    # Only valid when event_type == REJECTED (see model_validator below)

    @model_validator(mode="after")
    def validate_rejection_reason(self) -> "TimelineEventCreate":
        if self.rejection_reason_category is not None and self.event_type != TimelineEventType.REJECTED:
            raise ValueError("rejection_reason_category is only valid with event_type=REJECTED")
        return self

class TimelineEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    application_id: uuid.UUID
    event_type: TimelineEventType
    summary: str | None
    note: str | None
    occurred_at: datetime
    importance: TimelineImportance
    follow_up_date: datetime | None
    source: str
    created_at: datetime
    updated_at: datetime
```

`RejectionReasonCategory` is imported from `schemas/application.py` (the enum
already exists from migration 0009).

### 5.2 Repository (`repositories/timeline_event.py`)

Extends `BaseRepository[TimelineEvent]`. **Does NOT use `list_paginated`** (it
orders by `created_at`, but the timeline hot path orders by `occurred_at`).

```python
class TimelineEventRepository(BaseRepository[TimelineEvent]):
    async def list_for_application(
        self, user_id: uuid.UUID, application_id: uuid.UUID
    ) -> Sequence[TimelineEvent]:
        """All events for one application, oldest-first (narrative order)."""
        stmt = (
            select(TimelineEvent)
            .where(
                TimelineEvent.user_id == user_id,
                TimelineEvent.application_id == application_id,
            )
            .order_by(TimelineEvent.occurred_at.asc(), TimelineEvent.id.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, user_id: uuid.UUID, data: TimelineEventCreate) -> TimelineEvent: ...
    async def get(self, user_id: uuid.UUID, event_id: uuid.UUID) -> TimelineEvent | None: ...

    async def delete(self, event: TimelineEvent) -> None:
        """Hard delete — TimelineEvent has no SoftDeleteMixin."""
        await self.session.delete(event)
        await self.session.flush()
```

No `deleted_at` filter (hard delete, Document pattern). No pagination (matches
`/applications/{id}/history` precedent; returns `list[]`).

### 5.3 Service (`services/timeline_event.py`)

Module-level functions, `(session, user, ...)` signature.

```python
async def list_events(session, user, application_id) -> list[TimelineEventRead]:
    repo = TimelineEventRepository(session)
    events = await repo.list_for_application(user.id, application_id)
    return [TimelineEventRead.model_validate(e) for e in events]

async def create_event(session, user, data: TimelineEventCreate) -> TimelineEventRead:
    # 1. Validate application ownership (NotFoundError if missing/owned by other)
    app_repo = ApplicationRepository(session)
    application = await app_repo.get(user.id, data.application_id)
    if application is None:
        raise NotFoundError(f"Application {data.application_id} not found")

    # 2. Create the event
    repo = TimelineEventRepository(session)
    event = await repo.create(user.id, data)

    # 3. If REJECTED with a reason, update the application's rejection fields
    #    (drives analytics — A2 in the roadmap).
    if data.event_type == TimelineEventType.REJECTED and data.rejection_reason_category:
        application.rejection_reason_category = data.rejection_reason_category
        if data.summary:
            application.rejection_reason = data.summary
        await session.flush()

    return TimelineEventRead.model_validate(event)

async def delete_event(session, user, event_id) -> None:
    repo = TimelineEventRepository(session)
    event = await repo.get(user.id, event_id)
    if event is None:
        raise NotFoundError(f"Timeline event {event_id} not found")
    await repo.delete(event)
```

Transactions: service calls `flush()` only; `commit()` happens in
`get_session` dependency (existing pattern).

### 5.4 Routes (`api/v1/routes/timeline_events.py`)

```python
router = APIRouter(prefix="/timeline-events", tags=["timeline-events"])

@router.get("", response_model=list[TimelineEventRead])
async def list_timeline_events(
    session: SessionDep, current_user: CurrentUserDep,
    application_id: uuid.UUID = Query(...),   # required filter
) -> list[TimelineEventRead]: ...

@router.post("", response_model=TimelineEventRead, status_code=201)
async def create_timeline_event(
    session: SessionDep, current_user: CurrentUserDep,
    data: TimelineEventCreate,
) -> TimelineEventRead: ...

@router.delete("/{event_id}", status_code=204)
async def delete_timeline_event(
    session: SessionDep, current_user: CurrentUserDep,
    event_id: uuid.UUID,
) -> Response: ...   # returns 204 No Content
```

Register in `main.py` alongside other routers.

---

## 6. Frontend — structure

### 6.1 Types (`types/index.ts`)

```ts
export type TimelineEventType =
  | "APPLIED" | "EMAIL" | "CALL" | "FOLLOW_UP" | "PHONE_SCREEN"
  | "TECHNICAL" | "SYSTEM_DESIGN" | "ONSITE" | "TAKE_HOME"
  | "RECRUITER_MESSAGE" | "OFFER" | "ACCEPTED" | "REJECTED"
  | "NOTE" | "CUSTOM"

export type TimelineImportance = "NORMAL" | "IMPORTANT" | "MILESTONE"
export type RejectionReasonCategory =
  | "visa_sponsorship" | "lack_of_experience" | "salary"
  | "culture_fit" | "position_filled" | "no_feedback" | "other"

export interface TimelineEvent {
  id: string
  application_id: string
  event_type: TimelineEventType
  summary: string | null
  note: string | null
  occurred_at: string
  importance: TimelineImportance
  follow_up_date: string | null
  source: string
  created_at: string
  updated_at: string
}
```

### 6.2 Centralized metadata (`utils/timeline.ts`)

Single source of truth for how each event type renders. Prevents icon/label
scattering across components. (Lives in `utils/` per AGENTS.md — there is no
`lib/` directory.)

```ts
import { type LucideIcon, Mail, Phone, ... } from "lucide-react"

type EventMeta = {
  label: string          // human-readable: "Phone Screen"
  icon: LucideIcon
  description: string    // short hint for the form
  tone: "primary" | "muted" | "success" | "danger"
}

export const EVENT_METADATA: Record<TimelineEventType, EventMeta> = {
  APPLIED:          { label: "Applied",           icon: Send,      ... },
  EMAIL:            { label: "Email",             icon: Mail,      ... },
  CALL:             { label: "Call",              icon: Phone,     ... },
  FOLLOW_UP:        { label: "Follow-up",         icon: Reply,     ... },
  PHONE_SCREEN:     { label: "Phone Screen",      icon: PhoneCall, ... },
  TECHNICAL:        { label: "Technical",         icon: Code,      ... },
  SYSTEM_DESIGN:    { label: "System Design",     icon: Network,   ... },
  ONSITE:           { label: "Onsite",            icon: Building,  ... },
  TAKE_HOME:        { label: "Take-home",         icon: FileCode,  ... },
  RECRUITER_MESSAGE:{ label: "Recruiter Message", icon: MessageSquare, ... },
  OFFER:            { label: "Offer",             icon: Trophy,    ... },
  ACCEPTED:         { label: "Accepted",          icon: CheckCircle2, ... },
  REJECTED:         { label: "Rejected",          icon: XCircle,   ... },
  NOTE:             { label: "Note",              icon: StickyNote,... },
  CUSTOM:           { label: "Custom",            icon: Plus,      ... },
}

export const IMPORTANCE_METADATA: Record<TimelineImportance, { label: string; ... }> = { ... }

export const REJECTION_CATEGORIES: { value: RejectionReasonCategory; label: string }[] = [
  { value: "visa_sponsorship", label: "Visa Sponsorship" },
  ...
]
```

### 6.3 Merge logic (`utils/timeline.ts` — same file)

**The component does not merge.** A pure function owns the merge + normalization
so it is testable and reusable. Lives in the same `utils/timeline.ts` as the
metadata (§6.2).

```ts
export type TimelineEntry = {
  id: string
  kind: "stage" | "event" | "applied" | "terminal"
  icon: LucideIcon
  tone: "primary" | "muted" | "success" | "danger"
  title: string
  subtitle: string | null
  note: string | null
  at: string                       // ISO timestamp for sorting
  atLabel: string                  // formatted for display
  importance: TimelineImportance
}

export function buildTimeline(
  application: Application,
  history: StageHistory[],
  events: TimelineEvent[],
): TimelineEntry[] {
  // 1. Synthetic "Applied" entry (from applied_at ?? created_at).
  // 2. Stage transitions (from history, by changed_at).
  // 3. Custom events (from events, by occurred_at).
  // 4. Terminal marker if accepted/rejected (if no explicit event covers it).
  // 5. Merge all three streams, sort ascending by timestamp (oldest first).
  // 6. Map event_type → icon/tone via EVENT_METADATA.
}
```

### 6.4 API client (`services/api-client.ts`)

```ts
export async function listTimelineEvents(applicationId: string): Promise<TimelineEvent[]> {
  return unwrapList(await apiFetch<PageOut<TimelineEvent> | TimelineEvent[]>(
    `/timeline-events?application_id=${applicationId}`,
  ))
}
```

Mirrors `listStageHistory` exactly (server-side, non-paginated).

### 6.5 Server actions (`features/applications/timeline-actions.ts`)

```ts
"use server"

export async function createTimelineEvent(formData: FormData): Promise<ActionResult> { ... }
// - Reads: application_id (hidden), event_type, summary, note, occurred_at, importance,
//   rejection_reason_category (only sent when event_type=REJECTED).
// - POST /timeline-events
// - revalidatePath(`/applications/${applicationId}`)

export async function deleteTimelineEvent(eventId: string, applicationId: string): Promise<ActionResult> { ... }
// - DELETE /timeline-events/{eventId}
// - revalidatePath(`/applications/${applicationId}`)
```

Standard `ActionResult` + `errorMessage` helpers (copied from existing
`actions.ts` pattern). `deleteTimelineEvent` binds `eventId` + `applicationId`
in the client.

---

## 7. Frontend — components

### 7.1 `ApplicationTimeline` (updated — stays a Server Component)

Props: `{ application, history, events }`. **Only renders** — calls
`buildTimeline()` and maps `TimelineEntry[]` to the existing `<ol>` markup.
Importance drives visual weight (MILESTONE → larger icon, bold).

### 7.2 `AddEventForm` (`features/applications/add-event-form.tsx`) — Client

- `"use client"`, shadcn `Dialog`, trigger `<Button variant="outline" size="sm">Add Event</Button>`.
- `useActionState(createTimelineEvent, { ok: false })`.
- Fields:
  - `event_type` — `<Select>` populated from `EVENT_METADATA`. Default `NOTE`.
  - `summary` — `<Input>`, optional, `maxLength=255`. Placeholder changes by
    type ("Phone Screen with Sarah", "Salary discussion").
  - `note` — `<Textarea>`, optional.
  - `importance` — `<Select>`: Normal / Important / Milestone. Default Normal.
  - `occurred_at` — `<Input type="datetime-local">`. Optional; default now.
  - `rejection_reason_category` — **conditionally rendered** `<Select>` (only
    when `event_type === "REJECTED"`), populated from `REJECTION_CATEGORIES`.
  - `application_id` — hidden input.
- When `event_type === "CUSTOM"`, `summary` becomes **required** (the typed
  title replaces the type label in the timeline).
- Native HTML validation; toast feedback on success/error.

### 7.3 Delete confirmation

Delete is **never instant**. A shadcn `AlertDialog` wraps the delete trigger:
"Delete this event? This can't be undone." → confirm calls
`deleteTimelineEvent`.

---

## 8. Attachments (deferred — schema-ready)

Not built in F2. The design accommodates them without a later rewrite:

**Future table** `timeline_event_attachments`:
```
id, timeline_event_id (FK CASCADE), document_id (FK CASCADE),
created_at
```

This links events to the existing `documents` table (which already supports
resume, cover_letter, certificate, etc.). No column on `timeline_events` today;
no migration blocker. When built, the `AddEventForm` gains an attachment
uploader after the event is created.

---

## 9. Search (deferred — documented)

Future: `GET /timeline-events?application_id=...&q=salary` → full-text search
on `summary` + `note`. Add a `pg_trgm` GIN index or `ILIKE` filter. The `note`
column is already `Text`. Not built in F2.

---

## 10. Activity Feed evolution (the `source` column)

The `source` column (default `'user'`) is the future-proofing enabler:

| `source` value | Who creates | Example | Deletable? |
|---|---|---|---|
| `user` (F2) | The user via "Add Event" | Phone screen, note, follow-up | Yes |
| `system` (future) | Backend on a side-effect | "Resume v3 attached", "Stage moved to Interview", "Reminder completed" | No (audit trail) |
| `import` (future) | Bulk import tool | "Imported from LinkedIn" | No |

**F2 only writes `source='user'`.** The column exists so system events can be
added later without a migration. The `TimelineEventRead` schema already exposes
`source`, so the frontend can render a subtle "auto" badge on non-user events
when they eventually appear.

---

## 11. Files to create / modify

### Backend (create)
- `backend/alembic/versions/0010_timeline_event_enrichment.py`
- `backend/src/careeros_api/schemas/timeline_event.py`
- `backend/src/careeros_api/repositories/timeline_event.py`
- `backend/src/careeros_api/services/timeline_event.py`
- `backend/src/careeros_api/api/v1/routes/timeline_events.py`
- `backend/tests/test_timeline_events.py`

### Backend (modify)
- `backend/src/careeros_api/models/timeline_event.py` — enum types, column changes.
- `backend/src/careeros_api/main.py` — register router.

### Frontend (create)
- `frontend/src/utils/timeline.ts` — centralized metadata + `buildTimeline()` merge logic.
- `frontend/src/features/applications/timeline-actions.ts` — server actions.
- `frontend/src/features/applications/add-event-form.tsx` — "Add Event" dialog.

### Frontend (modify)
- `frontend/src/types/index.ts` — add types.
- `frontend/src/services/api-client.ts` — add `listTimelineEvents`.
- `frontend/src/features/applications/application-timeline.tsx` — render from `buildTimeline()`.
- `frontend/src/app/(app)/applications/[id]/page.tsx` — fetch events, pass to timeline + form.

---

## 12. Verification

**Backend:**
- `uv run ruff check .` clean
- `uv run ruff format --check .` clean
- `uv run mypy src` clean (strict)
- `uv run --extra dev pytest` green — tests cover: create, list, delete,
  isolation (user A cannot see/delete user B's events), REJECTED sets
  application rejection fields, non-owned application_id → 404.
- `uv run alembic upgrade head` applies 0010 cleanly; `downgrade` reverses.
- Unauthenticated request to `/timeline-events` → 401 problem+json.

**Frontend:**
- `pnpm lint` clean
- `pnpm typecheck` clean
- `pnpm build` succeeds

**Manual smoke (Docker):**
- Add an event via the workspace → appears in timeline immediately.
- Add a REJECTED event with reason → application's rejection fields updated.
- Delete an event → confirmation dialog → event gone after confirm.
- Timeline merges stage moves + custom events chronologically.
