# F2 — Custom Timeline Events Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a user add custom activity events (phone screens, emails, follow-ups, notes) to an application's timeline, with a native event_type enum, importance levels, rejection-reason capture, and a merged chronological view.

**Architecture:** Backend follows the existing clean-architecture layers (routes → services → repositories → models) mirroring the `notes` feature. A migration (`0010`) converts `event_type` from a free string to a native enum and adds `importance`, `follow_up_date`, `source`, and renames `title` → `summary`. Frontend uses Server Actions for mutations and a pure `buildTimeline()` function for the 3-way merge (stage history + custom events + synthetic "Applied").

**Tech Stack:** FastAPI · SQLAlchemy 2 async · Alembic · Pydantic v2 (backend); Next.js 15 · React 19 · Server Actions · shadcn/ui (frontend).

**Spec:** `docs/superpowers/specs/2026-07-27-timeline-events-design.md`

---

## File Structure

### Backend (create)
| File | Responsibility |
|---|---|
| `backend/alembic/versions/0010_timeline_event_enrichment.py` | Migration: enum conversion, column adds/rename |
| `backend/src/careeros_api/schemas/timeline_event.py` | Pydantic Create/Read schemas + rejection validator |
| `backend/src/careeros_api/repositories/timeline_event.py` | Data access (list_for_application, create, get, hard delete) |
| `backend/src/careeros_api/services/timeline_event.py` | Business logic + application ownership check + rejection sync |
| `backend/src/careeros_api/api/v1/routes/timeline_events.py` | GET/POST/DELETE endpoints |
| `backend/tests/test_timeline_events.py` | Endpoint tests (CRUD, isolation, rejection sync) |

### Backend (modify)
| File | Change |
|---|---|
| `backend/src/careeros_api/models/timeline_event.py` | Add enums, change event_type column, rename title→summary, add columns |
| `backend/src/careeros_api/main.py` | Register the timeline_events router |

### Frontend (create)
| File | Responsibility |
|---|---|
| `frontend/src/utils/timeline.ts` | Centralized event metadata (icon/label/tone) + `buildTimeline()` merge |
| `frontend/src/features/applications/timeline-actions.ts` | Server Actions: createTimelineEvent, deleteTimelineEvent |
| `frontend/src/features/applications/add-event-form.tsx` | Client dialog for adding events |
| `frontend/src/features/applications/delete-event-dialog.tsx` | Client AlertDialog for delete confirmation |

### Frontend (modify)
| File | Change |
|---|---|
| `frontend/src/types/index.ts` | Add TimelineEvent, TimelineEventType, TimelineImportance, RejectionReasonCategory |
| `frontend/src/services/api-client.ts` | Add `listTimelineEvents()` |
| `frontend/src/features/applications/application-timeline.tsx` | Render from `buildTimeline()` instead of inline merge |
| `frontend/src/app/(app)/applications/[id]/page.tsx` | Fetch events, pass to timeline + AddEventForm |

---

## Task 1: Migration 0010 — enrich timeline_events

**Files:**
- Create: `backend/alembic/versions/0010_timeline_event_enrichment.py`

- [ ] **Step 1: Create the migration file**

```python
"""timeline event enrichment: enum, importance, follow-up, source, summary rename

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-27 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


timeline_event_type = postgresql.ENUM(
    "APPLIED",
    "EMAIL",
    "CALL",
    "FOLLOW_UP",
    "PHONE_SCREEN",
    "TECHNICAL",
    "SYSTEM_DESIGN",
    "ONSITE",
    "TAKE_HOME",
    "RECRUITER_MESSAGE",
    "OFFER",
    "ACCEPTED",
    "REJECTED",
    "NOTE",
    "CUSTOM",
    name="timeline_event_type",
)

timeline_importance = postgresql.ENUM(
    "NORMAL",
    "IMPORTANT",
    "MILESTONE",
    name="timeline_importance",
)


def upgrade() -> None:
    timeline_event_type.create(op.get_bind(), checkfirst=False)
    timeline_importance.create(op.get_bind(), checkfirst=False)

    op.alter_column(
        "timeline_events",
        "event_type",
        type_=timeline_event_type,
        postgresql_using="event_type::text",
        existing_type=sa.String(length=64),
        existing_nullable=False,
    )

    op.alter_column("timeline_events", "title", new_column_name="summary")

    op.add_column(
        "timeline_events",
        sa.Column(
            "importance",
            timeline_importance,
            nullable=False,
            server_default="NORMAL",
        ),
    )
    op.add_column(
        "timeline_events",
        sa.Column("follow_up_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "timeline_events",
        sa.Column(
            "source",
            sa.String(length=32),
            nullable=False,
            server_default="user",
        ),
    )


def downgrade() -> None:
    op.drop_column("timeline_events", "source")
    op.drop_column("timeline_events", "follow_up_date")
    op.drop_column("timeline_events", "importance")

    op.alter_column("timeline_events", "summary", new_column_name="title")

    op.alter_column(
        "timeline_events",
        "event_type",
        type_=sa.String(length=64),
        postgresql_using="event_type::text",
        existing_type=timeline_event_type,
        existing_nullable=False,
    )

    timeline_importance.drop(op.get_bind(), checkfirst=False)
    timeline_event_type.drop(op.get_bind(), checkfirst=False)
```

- [ ] **Step 2: Verify migration applies and reverses**

Run (requires a running Postgres on port 5433 — use Docker):

```bash
cd backend
uv run alembic upgrade head
```

Expected: `0010` applied with no errors.

```bash
uv run alembic downgrade 0009
```

Expected: rolls back cleanly.

```bash
uv run alembic upgrade head
```

Expected: re-applies `0010`.

- [ ] **Step 3: Commit**

```bash
git add backend/alembic/versions/0010_timeline_event_enrichment.py
git commit -m "feat(db): 0010 — timeline event enum, importance, follow-up, source, summary rename"
```

---

## Task 2: Update the TimelineEvent ORM model

**Files:**
- Modify: `backend/src/careeros_api/models/timeline_event.py`

- [ ] **Step 1: Rewrite the model with enums and new columns**

Replace the entire file content with:

```python
"""Timeline event ORM model.

A free-form activity log entry on an application (recruiter viewed, email sent,
phone screen, take-home, note, custom …). Lives **alongside**
``application_stage_history`` (which records stage transitions only); the
workspace timeline merges both, ordered by time.

``event_type`` is a native enum with a ``CUSTOM`` escape hatch — the UI shows a
free-text ``summary`` when the user picks ``CUSTOM``. ``source`` defaults to
``'user'`` and exists so the table can later hold system-generated activity
entries without a migration.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from careeros_api.db.base import Base
from careeros_api.db.mixins import TimestampMixin, UUIDPrimaryKey


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


class TimelineEvent(UUIDPrimaryKey, TimestampMixin, Base):
    """A single dated activity entry on an application's timeline."""

    __tablename__ = "timeline_events"
    __table_args__ = (
        Index(
            "ix_timeline_events_application_id_occurred_at",
            "application_id",
            "occurred_at",
            "id",
        ),
        Index("ix_timeline_events_user_id_occurred_at", "user_id", "occurred_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[TimelineEventType] = mapped_column(
        sa.Enum(TimelineEventType, name="timeline_event_type"),
        nullable=False,
    )
    summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    importance: Mapped[TimelineImportance] = mapped_column(
        sa.Enum(TimelineImportance, name="timeline_importance"),
        nullable=False,
        default=TimelineImportance.NORMAL,
        server_default="NORMAL",
    )
    follow_up_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="user",
        server_default="user",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<TimelineEvent {self.event_type!r} @ {self.occurred_at}>"


__all__ = ["TimelineEvent", "TimelineEventType", "TimelineImportance"]
```

- [ ] **Step 2: Verify the model imports cleanly**

```bash
cd backend
uv run python -c "from careeros_api.models.timeline_event import TimelineEvent, TimelineEventType, TimelineImportance; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/src/careeros_api/models/timeline_event.py
git commit -m "feat(models): timeline event — enum event_type, importance, summary rename"
```

---

## Task 3: Pydantic schemas

**Files:**
- Create: `backend/src/careeros_api/schemas/timeline_event.py`

- [ ] **Step 1: Create the schema file**

```python
"""Timeline event request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from careeros_api.models.application import rejection_reason_category
from careeros_api.models.timeline_event import TimelineEventType, TimelineImportance


class TimelineEventBase(BaseModel):
    """Fields shared across create/read schemas."""

    application_id: uuid.UUID
    event_type: TimelineEventType
    summary: str | None = Field(default=None, max_length=255)
    note: str | None = None
    occurred_at: datetime | None = None
    importance: TimelineImportance = TimelineImportance.NORMAL


class TimelineEventCreate(TimelineEventBase):
    """Payload to create a timeline event.

    ``rejection_reason_category`` is only valid when ``event_type`` is
    ``REJECTED``; the validator below enforces that invariant.
    """

    rejection_reason_category: str | None = None

    @model_validator(mode="after")
    def _validate_rejection_reason(self) -> TimelineEventCreate:
        if (
            self.rejection_reason_category is not None
            and self.event_type != TimelineEventType.REJECTED
        ):
            raise ValueError(
                "rejection_reason_category is only valid when event_type is REJECTED"
            )
        return self


class TimelineEventRead(BaseModel):
    """Public representation of a timeline event."""

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

- [ ] **Step 2: Verify it imports**

```bash
cd backend
uv run python -c "from careeros_api.schemas.timeline_event import TimelineEventCreate, TimelineEventRead; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/src/careeros_api/schemas/timeline_event.py
git commit -m "feat(api): timeline event pydantic schemas with rejection validator"
```

---

## Task 4: Repository

**Files:**
- Create: `backend/src/careeros_api/repositories/timeline_event.py`

- [ ] **Step 1: Create the repository file**

```python
"""Repository for the ``TimelineEvent`` model (all reads scoped by ``user_id``)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.models.timeline_event import TimelineEvent
from careeros_api.repositories.base import BaseRepository
from careeros_api.schemas.timeline_event import TimelineEventCreate


class TimelineEventRepository(BaseRepository[TimelineEvent]):
    """Data access for timeline events belonging to a single user."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TimelineEvent)

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
            .order_by(
                TimelineEvent.occurred_at.asc(),
                TimelineEvent.id.asc(),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get(
        self, user_id: uuid.UUID, event_id: uuid.UUID
    ) -> TimelineEvent | None:
        """Return the event if it exists and belongs to ``user_id``."""
        stmt = select(TimelineEvent).where(
            TimelineEvent.id == event_id,
            TimelineEvent.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self, user_id: uuid.UUID, data: TimelineEventCreate
    ) -> TimelineEvent:
        """Insert a new timeline event owned by ``user_id``."""
        payload = data.model_dump(exclude={"rejection_reason_category"})
        event = TimelineEvent(user_id=user_id, **payload)
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def delete(self, event: TimelineEvent) -> None:
        """Hard-delete ``event`` — TimelineEvent has no SoftDeleteMixin."""
        await self.session.delete(event)
        await self.session.flush()
```

- [ ] **Step 2: Verify it imports**

```bash
cd backend
uv run python -c "from careeros_api.repositories.timeline_event import TimelineEventRepository; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/src/careeros_api/repositories/timeline_event.py
git commit -m "feat(api): timeline event repository with occurred_at ordering"
```

---

## Task 5: Service

**Files:**
- Create: `backend/src/careeros_api/services/timeline_event.py`

- [ ] **Step 1: Create the service file**

```python
"""Timeline event business-logic services."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.errors import NotFoundError
from careeros_api.models.timeline_event import TimelineEventType
from careeros_api.models.user import User
from careeros_api.repositories.application import ApplicationRepository
from careeros_api.repositories.timeline_event import TimelineEventRepository
from careeros_api.schemas.timeline_event import (
    TimelineEventCreate,
    TimelineEventRead,
)


async def list_events(
    session: AsyncSession,
    user: User,
    application_id: uuid.UUID,
) -> list[TimelineEventRead]:
    """Return all timeline events for one application, oldest-first."""
    repo = TimelineEventRepository(session)
    events = await repo.list_for_application(user.id, application_id)
    return [TimelineEventRead.model_validate(e) for e in events]


async def create_event(
    session: AsyncSession,
    user: User,
    data: TimelineEventCreate,
) -> TimelineEventRead:
    """Create a timeline event for the caller.

    Validates that the application belongs to the user (raises
    ``NotFoundError`` otherwise, to avoid leaking existence). When the event
    type is ``REJECTED`` and a reason category is provided, the application's
    rejection fields are updated so analytics can aggregate them.
    """
    app_repo = ApplicationRepository(session)
    application = await app_repo.get(user.id, data.application_id)
    if application is None:
        raise NotFoundError(f"Application {data.application_id} not found")

    repo = TimelineEventRepository(session)
    event = await repo.create(user.id, data)

    if (
        data.event_type == TimelineEventType.REJECTED
        and data.rejection_reason_category is not None
    ):
        application.rejection_reason_category = data.rejection_reason_category
        if data.summary:
            application.rejection_reason = data.summary
        await session.flush()

    return TimelineEventRead.model_validate(event)


async def delete_event(
    session: AsyncSession,
    user: User,
    event_id: uuid.UUID,
) -> None:
    """Hard-delete a timeline event owned by the caller."""
    repo = TimelineEventRepository(session)
    event = await repo.get(user.id, event_id)
    if event is None:
        raise NotFoundError(f"Timeline event {event_id} not found")
    await repo.delete(event)
```

- [ ] **Step 2: Verify it imports**

```bash
cd backend
uv run python -c "from careeros_api.services.timeline_event import create_event, list_events, delete_event; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/src/careeros_api/services/timeline_event.py
git commit -m "feat(api): timeline event service with rejection-reason sync"
```

---

## Task 6: Routes + registration

**Files:**
- Create: `backend/src/careeros_api/api/v1/routes/timeline_events.py`
- Modify: `backend/src/careeros_api/main.py`

- [ ] **Step 1: Create the routes file**

```python
"""Endpoints for the authenticated user's timeline events (``/api/v1/timeline-events``)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Response, status

from careeros_api.api.deps import CurrentUserDep, SessionDep
from careeros_api.schemas.timeline_event import (
    TimelineEventCreate,
    TimelineEventRead,
)
from careeros_api.services import timeline_event as timeline_event_service

router = APIRouter(prefix="/timeline-events", tags=["timeline-events"])


@router.get("", response_model=list[TimelineEventRead])
async def list_timeline_events(
    session: SessionDep,
    current_user: CurrentUserDep,
    application_id: uuid.UUID = Query(...),
) -> list[TimelineEventRead]:
    """List all timeline events for one application, oldest-first."""
    return await timeline_event_service.list_events(
        session, current_user, application_id
    )


@router.post(
    "",
    response_model=TimelineEventRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_timeline_event(
    session: SessionDep,
    current_user: CurrentUserDep,
    data: TimelineEventCreate,
) -> TimelineEventRead:
    """Create a new timeline event for the caller."""
    return await timeline_event_service.create_event(session, current_user, data)


@router.delete("/{event_id}")
async def delete_timeline_event(
    session: SessionDep,
    current_user: CurrentUserDep,
    event_id: uuid.UUID,
) -> Response:
    """Hard-delete a timeline event owned by the caller."""
    await timeline_event_service.delete_event(session, current_user, event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

- [ ] **Step 2: Register the router in main.py**

In `backend/src/careeros_api/main.py`, add `timeline_events` to the import block (after `tags,` on line 26):

```python
from careeros_api.api.v1.routes import (
    ai,
    analytics,
    applications,
    billing,
    companies,
    contacts,
    documents,
    health,
    interviews,
    me,
    notes,
    pipeline,
    reminders,
    tags,
    timeline_events,
)
```

Then add the include_router call after the `tags` line (line 78):

```python
    app.include_router(tags.router, prefix="/api/v1")
    app.include_router(timeline_events.router, prefix="/api/v1")
    app.include_router(ai.router, prefix="/api/v1")
```

- [ ] **Step 3: Verify the app starts and the route is registered**

```bash
cd backend
uv run python -c "from careeros_api.main import app; routes = [r.path for r in app.routes]; print(any('timeline-events' in r for r in routes))"
```

Expected: `True`

- [ ] **Step 4: Commit**

```bash
git add backend/src/careeros_api/api/v1/routes/timeline_events.py backend/src/careeros_api/main.py
git commit -m "feat(api): timeline events endpoints (GET/POST/DELETE /timeline-events)"
```

---

## Task 7: Backend tests

**Files:**
- Create: `backend/tests/test_timeline_events.py`

- [ ] **Step 1: Create the test file**

```python
"""Tests for the ``/api/v1/timeline-events`` endpoints."""

from __future__ import annotations

from httpx import AsyncClient

from tests.helpers import AuthHeaders


async def _create_company(
    client: AsyncClient, headers: dict[str, str], name: str
) -> str:
    response = await client.post("/api/v1/companies", headers=headers, json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_application(
    client: AsyncClient, headers: dict[str, str], company_id: str
) -> str:
    response = await client.post(
        "/api/v1/applications",
        headers=headers,
        json={"company_id": company_id, "role_title": "Engineer"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_timeline_events_without_auth_returns_401(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/timeline-events?application_id=00000000-0000-0000-0000-000000000000")).status_code == 401


async def test_create_and_list_event(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _create_company(client, headers, "Acme")
    application_id = await _create_application(client, headers, company_id)

    created = await client.post(
        "/api/v1/timeline-events",
        headers=headers,
        json={
            "application_id": application_id,
            "event_type": "PHONE_SCREEN",
            "summary": "Phone screen with Sarah",
            "note": "Discussed backend architecture",
            "importance": "IMPORTANT",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["event_type"] == "PHONE_SCREEN"
    assert body["summary"] == "Phone screen with Sarah"
    assert body["importance"] == "IMPORTANT"
    assert body["source"] == "user"

    listed = await client.get(
        f"/api/v1/timeline-events?application_id={application_id}",
        headers=headers,
    )
    assert listed.status_code == 200, listed.text
    events = listed.json()
    assert len(events) == 1
    assert events[0]["id"] == body["id"]


async def test_delete_event(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _create_company(client, headers, "Acme")
    application_id = await _create_application(client, headers, company_id)

    created = await client.post(
        "/api/v1/timeline-events",
        headers=headers,
        json={"application_id": application_id, "event_type": "NOTE"},
    )
    event_id = created.json()["id"]

    deleted = await client.delete(
        f"/api/v1/timeline-events/{event_id}", headers=headers
    )
    assert deleted.status_code == 204

    listed = await client.get(
        f"/api/v1/timeline-events?application_id={application_id}",
        headers=headers,
    )
    assert len(listed.json()) == 0


async def test_create_event_unknown_application_returns_404(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    response = await client.post(
        "/api/v1/timeline-events",
        headers=headers,
        json={
            "application_id": "00000000-0000-0000-0000-000000000000",
            "event_type": "NOTE",
        },
    )
    assert response.status_code == 404


async def test_events_isolated_per_user(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers_a = auth()
    company_id = await _create_company(client, headers_a, "Acme")
    application_id = await _create_application(client, headers_a, company_id)
    await client.post(
        "/api/v1/timeline-events",
        headers=headers_a,
        json={"application_id": application_id, "event_type": "EMAIL"},
    )

    headers_b = auth(sub="user_b", email="b@example.com")
    listed_b = await client.get(
        f"/api/v1/timeline-events?application_id={application_id}",
        headers=headers_b,
    )
    assert listed_b.status_code == 200
    assert len(listed_b.json()) == 0


async def test_delete_event_from_other_user_returns_404(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers_a = auth()
    company_id = await _create_company(client, headers_a, "Acme")
    application_id = await _create_application(client, headers_a, company_id)
    created = await client.post(
        "/api/v1/timeline-events",
        headers=headers_a,
        json={"application_id": application_id, "event_type": "NOTE"},
    )
    event_id = created.json()["id"]

    headers_b = auth(sub="user_b", email="b@example.com")
    deleted = await client.delete(
        f"/api/v1/timeline-events/{event_id}", headers=headers_b
    )
    assert deleted.status_code == 404


async def test_rejected_event_sets_application_rejection(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _create_company(client, headers, "Acme")
    application_id = await _create_application(client, headers, company_id)

    response = await client.post(
        "/api/v1/timeline-events",
        headers=headers,
        json={
            "application_id": application_id,
            "event_type": "REJECTED",
            "summary": "Went with another candidate",
            "rejection_reason_category": "position_filled",
        },
    )
    assert response.status_code == 201, response.text

    application = await client.get(
        f"/api/v1/applications/{application_id}", headers=headers
    )
    assert application.json()["rejection_reason_category"] == "position_filled"
    assert application.json()["rejection_reason"] == "Went with another candidate"


async def test_rejection_reason_only_valid_with_rejected(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _create_company(client, headers, "Acme")
    application_id = await _create_application(client, headers, company_id)

    response = await client.post(
        "/api/v1/timeline-events",
        headers=headers,
        json={
            "application_id": application_id,
            "event_type": "NOTE",
            "rejection_reason_category": "salary",
        },
    )
    assert response.status_code == 422
```

- [ ] **Step 2: Run the tests (requires Docker Postgres on port 5433)**

```bash
cd backend
uv run --extra dev pytest tests/test_timeline_events.py -v
```

Expected: all tests pass (those needing a DB pass; if no DB, they skip).

- [ ] **Step 3: Run lint + typecheck**

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

Expected: all clean.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_timeline_events.py
git commit -m "test(api): timeline events CRUD, isolation, rejection-reason sync"
```

---

## Task 8: Frontend types + API client

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/services/api-client.ts`

- [ ] **Step 1: Add types to `types/index.ts`**

Add after the `StageHistory` interface (after line 108):

```ts
/** The type of a timeline activity event. CUSTOM lets the user define their own. */
export type TimelineEventType =
  | "APPLIED"
  | "EMAIL"
  | "CALL"
  | "FOLLOW_UP"
  | "PHONE_SCREEN"
  | "TECHNICAL"
  | "SYSTEM_DESIGN"
  | "ONSITE"
  | "TAKE_HOME"
  | "RECRUITER_MESSAGE"
  | "OFFER"
  | "ACCEPTED"
  | "REJECTED"
  | "NOTE"
  | "CUSTOM"

/** How much an event matters (drives timeline visual weight + future filtering). */
export type TimelineImportance = "NORMAL" | "IMPORTANT" | "MILESTONE"

/** Structured rejection categories powering analytics. */
export type RejectionReasonCategory =
  | "visa_sponsorship"
  | "lack_of_experience"
  | "salary"
  | "culture_fit"
  | "position_filled"
  | "no_feedback"
  | "other"

/** A user-authored activity event on an application timeline. */
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

- [ ] **Step 2: Add `TimelineEvent` import + `listTimelineEvents` to api-client.ts**

In the import block (lines 3-19), add `TimelineEvent`:

```ts
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
  Tag,
  TimelineEvent,
} from "@/types"
```

Add after `listDocuments` (after line 154):

```ts
/** Fetch timeline events for an application, oldest first. */
export async function listTimelineEvents(applicationId: string): Promise<TimelineEvent[]> {
  const data = await apiFetch<PageOut<TimelineEvent> | TimelineEvent[]>(
    `/timeline-events?application_id=${encodeURIComponent(applicationId)}`,
  )
  return unwrapList(data)
}
```

- [ ] **Step 3: Verify typecheck**

```bash
cd frontend
pnpm typecheck
```

Expected: clean.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/services/api-client.ts
git commit -m "feat(frontend): timeline event types + listTimelineEvents client"
```

---

## Task 9: Centralized metadata + merge logic

**Files:**
- Create: `frontend/src/utils/timeline.ts`

- [ ] **Step 1: Create the metadata + merge file**

```ts
import {
  ArrowRight,
  Building2,
  CheckCircle2,
  Code,
  FileCode,
  Mail,
  MessageSquare,
  Network,
  Phone,
  PhoneCall,
  Plus,
  Reply,
  Send,
  StickyNote,
  Trophy,
  XCircle,
  type LucideIcon,
} from "lucide-react"

import type {
  Application,
  StageHistory,
  TimelineEvent,
  TimelineEventType,
  TimelineImportance,
} from "@/types"

/** How an event type renders — label, icon, tone. Centralized to prevent scattering. */
type EventMeta = {
  label: string
  icon: LucideIcon
  tone: "primary" | "muted" | "success" | "danger"
}

export const EVENT_METADATA: Record<TimelineEventType, EventMeta> = {
  APPLIED: { label: "Applied", icon: Send, tone: "primary" },
  EMAIL: { label: "Email", icon: Mail, tone: "muted" },
  CALL: { label: "Call", icon: Phone, tone: "muted" },
  FOLLOW_UP: { label: "Follow-up", icon: Reply, tone: "muted" },
  PHONE_SCREEN: { label: "Phone Screen", icon: PhoneCall, tone: "primary" },
  TECHNICAL: { label: "Technical", icon: Code, tone: "primary" },
  SYSTEM_DESIGN: { label: "System Design", icon: Network, tone: "primary" },
  ONSITE: { label: "Onsite", icon: Building2, tone: "primary" },
  TAKE_HOME: { label: "Take-home", icon: FileCode, tone: "primary" },
  RECRUITER_MESSAGE: { label: "Recruiter Message", icon: MessageSquare, tone: "muted" },
  OFFER: { label: "Offer", icon: Trophy, tone: "success" },
  ACCEPTED: { label: "Accepted", icon: CheckCircle2, tone: "success" },
  REJECTED: { label: "Rejected", icon: XCircle, tone: "danger" },
  NOTE: { label: "Note", icon: StickyNote, tone: "muted" },
  CUSTOM: { label: "Custom", icon: Plus, tone: "muted" },
}

export const IMPORTANCE_METADATA: Record<
  TimelineImportance,
  { label: string; starCount: number }
> = {
  NORMAL: { label: "Normal", starCount: 0 },
  IMPORTANT: { label: "Important", starCount: 1 },
  MILESTONE: { label: "Milestone", starCount: 2 },
}

export const REJECTION_CATEGORIES: {
  value: string
  label: string
}[] = [
  { value: "visa_sponsorship", label: "Visa Sponsorship" },
  { value: "lack_of_experience", label: "Lack of Experience" },
  { value: "salary", label: "Salary" },
  { value: "culture_fit", label: "Culture Fit" },
  { value: "position_filled", label: "Position Filled" },
  { value: "no_feedback", label: "No Feedback" },
  { value: "other", label: "Other" },
]

/** A normalized, render-ready entry in the merged timeline. */
export type TimelineEntry = {
  id: string
  kind: "applied" | "stage" | "event" | "terminal"
  icon: LucideIcon
  tone: "primary" | "muted" | "success" | "danger"
  title: string
  subtitle: string | null
  note: string | null
  at: string
  atLabel: string
  importance: TimelineImportance
}

/**
 * Merge three data sources into one chronological timeline (oldest first).
 *
 * 1. Synthetic "Applied" entry (from applied_at ?? created_at).
 * 2. Stage transitions (from history, by changed_at).
 * 3. Custom events (from events, by occurred_at).
 *
 * The component calling this only renders — all merge + normalization logic
 * lives here so it is testable and reusable.
 */
export function buildTimeline(
  application: Application,
  history: StageHistory[],
  events: TimelineEvent[],
): TimelineEntry[] {
  const entries: TimelineEntry[] = []

  // 1. Synthetic "Applied" entry — always first chronologically.
  const appliedIso = application.applied_at ?? application.created_at
  entries.push({
    id: "applied",
    kind: "applied",
    icon: Send,
    tone: "primary",
    title: `Applied to ${application.company?.name ?? "company"}`,
    subtitle: application.role_title,
    note: null,
    at: appliedIso,
    atLabel: formatDate(appliedIso),
    importance: "IMPORTANT",
  })

  // 2. Stage transitions.
  for (const h of history) {
    const fromName = h.from_stage?.name
    const toName = h.to_stage.name
    entries.push({
      id: h.id,
      kind: "stage",
      icon: ArrowRight,
      tone: "muted",
      title: fromName ? `Moved from ${fromName} to ${toName}` : `Moved to ${toName}`,
      subtitle: null,
      note: h.note,
      at: h.changed_at,
      atLabel: formatTimestamp(h.changed_at),
      importance: "NORMAL",
    })
  }

  // 3. Custom events.
  for (const e of events) {
    const meta = EVENT_METADATA[e.event_type]
    entries.push({
      id: e.id,
      kind: "event",
      icon: meta.icon,
      tone: meta.tone,
      title: e.summary ?? meta.label,
      subtitle: e.event_type === "CUSTOM" ? null : meta.label,
      note: e.note,
      at: e.occurred_at,
      atLabel: formatTimestamp(e.occurred_at),
      importance: e.importance,
    })
  }

  // Sort all entries chronologically (oldest first = narrative order).
  entries.sort((a, b) => new Date(a.at).getTime() - new Date(b.at).getTime())

  return entries
}

function formatDate(value: string | null): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

function formatTimestamp(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}
```

- [ ] **Step 2: Verify typecheck**

```bash
cd frontend
pnpm typecheck
```

Expected: clean.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/utils/timeline.ts
git commit -m "feat(frontend): centralized timeline metadata + buildTimeline merge logic"
```

---

## Task 10: Server actions

**Files:**
- Create: `frontend/src/features/applications/timeline-actions.ts`

- [ ] **Step 1: Create the actions file**

```ts
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

export async function createTimelineEvent(formData: FormData): Promise<ActionResult> {
  const applicationId = textValue(formData, "application_id")
  const eventType = textValue(formData, "event_type")

  if (!applicationId) return { ok: false, error: "Application ID is missing." }
  if (!eventType) return { ok: false, error: "Event type is required." }

  const payload: Record<string, unknown> = {
    application_id: applicationId,
    event_type: eventType,
  }

  const summary = textValue(formData, "summary")
  if (summary) payload.summary = summary

  const note = textValue(formData, "note")
  if (note) payload.note = note

  const importance = textValue(formData, "importance")
  if (importance) payload.importance = importance

  const occurredAt = textValue(formData, "occurred_at")
  if (occurredAt) payload.occurred_at = new Date(occurredAt).toISOString()

  const rejectionCategory = textValue(formData, "rejection_reason_category")
  if (rejectionCategory) payload.rejection_reason_category = rejectionCategory

  try {
    await apiFetch("/timeline-events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    revalidatePath(`/applications/${applicationId}`)
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

export async function deleteTimelineEvent(
  eventId: string,
  applicationId: string,
): Promise<ActionResult> {
  try {
    await apiFetch(`/timeline-events/${eventId}`, { method: "DELETE" })
    revalidatePath(`/applications/${applicationId}`)
    return { ok: true }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}
```

- [ ] **Step 2: Verify lint**

```bash
cd frontend
pnpm lint
pnpm typecheck
```

Expected: clean.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/applications/timeline-actions.ts
git commit -m "feat(frontend): server actions for create/delete timeline event"
```

---

## Task 11: Add Event form

**Files:**
- Create: `frontend/src/features/applications/add-event-form.tsx`

- [ ] **Step 1: Create the AddEventForm component**

```tsx
"use client"

import { useActionState, useCallback, useEffect, useState, type ReactNode } from "react"
import { toast } from "sonner"

import {
  EVENT_METADATA,
  IMPORTANCE_METADATA,
  REJECTION_CATEGORIES,
} from "@/utils/timeline"
import type { TimelineEventType, TimelineImportance } from "@/types"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"

import { createTimelineEvent, type ActionResult } from "./timeline-actions"

type AddEventFormProps = {
  applicationId: string
  trigger: ReactNode
}

const EVENT_OPTIONS = Object.entries(EVENT_METADATA).map(([value, meta]) => ({
  value: value as TimelineEventType,
  label: meta.label,
}))

export function AddEventForm({ applicationId, trigger }: AddEventFormProps) {
  const [open, setOpen] = useState(false)
  const close = useCallback(() => setOpen(false), [])

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-[480px]">
        <AddEventFields applicationId={applicationId} onClose={close} />
      </DialogContent>
    </Dialog>
  )
}

type AddEventFieldsProps = {
  applicationId: string
  onClose: () => void
}

function AddEventFields({ applicationId, onClose }: AddEventFieldsProps) {
  const [eventType, setEventType] = useState<TimelineEventType>("NOTE")
  const [state, formAction, isPending] = useActionState<ActionResult, FormData>(
    createTimelineEvent,
    { ok: false },
  )

  useEffect(() => {
    if (state.ok) {
      toast.success("Event added")
      onClose()
    } else if (state.error) {
      toast.error(state.error)
    }
  }, [state, onClose])

  const isCustom = eventType === "CUSTOM"
  const isRejected = eventType === "REJECTED"

  return (
    <>
      <DialogHeader>
        <DialogTitle>Add event</DialogTitle>
        <DialogDescription>
          Log activity on this application — calls, emails, interviews, notes.
        </DialogDescription>
      </DialogHeader>

      <form action={formAction} className="space-y-4">
        <input type="hidden" name="application_id" value={applicationId} />

        <div className="space-y-2">
          <Label htmlFor="event_type">Type</Label>
          <Select
            name="event_type"
            value={eventType}
            onValueChange={(v) => setEventType(v as TimelineEventType)}
          >
            <SelectTrigger id="event_type">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {EVENT_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="summary">
            Summary {isCustom && <span className="text-destructive">*</span>}
          </Label>
          <Input
            id="summary"
            name="summary"
            maxLength={255}
            required={isCustom}
            placeholder={isCustom ? "Describe what happened" : "Optional — e.g. Phone screen with Sarah"}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="note">Note</Label>
          <Textarea
            id="note"
            name="note"
            rows={3}
            placeholder="Optional details about this event"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="importance">Importance</Label>
            <Select name="importance" defaultValue="NORMAL">
              <SelectTrigger id="importance">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.entries(IMPORTANCE_METADATA) as [TimelineImportance, { label: string }][]).map(
                  ([value, meta]) => (
                    <SelectItem key={value} value={value}>
                      {meta.label}
                    </SelectItem>
                  ),
                )}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="occurred_at">When</Label>
            <Input
              id="occurred_at"
              name="occurred_at"
              type="datetime-local"
            />
          </div>
        </div>

        {isRejected && (
          <div className="space-y-2">
            <Label htmlFor="rejection_reason_category">Rejection reason</Label>
            <Select name="rejection_reason_category">
              <SelectTrigger id="rejection_reason_category">
                <SelectValue placeholder="Select a reason (optional)" />
              </SelectTrigger>
              <SelectContent>
                {REJECTION_CATEGORIES.map((cat) => (
                  <SelectItem key={cat.value} value={cat.value}>
                    {cat.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <DialogFooter>
          <Button type="submit" disabled={isPending}>
            {isPending ? "Adding…" : "Add event"}
          </Button>
        </DialogFooter>
      </form>
    </>
  )
}
```

- [ ] **Step 2: Verify lint + typecheck**

```bash
cd frontend
pnpm lint
pnpm typecheck
```

Expected: clean.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/applications/add-event-form.tsx
git commit -m "feat(frontend): add event dialog form with conditional rejection reason"
```

---

## Task 12: Delete confirmation dialog

**Files:**
- Create: `frontend/src/features/applications/delete-event-dialog.tsx`

- [ ] **Step 1: Add the AlertDialog shadcn primitive**

```bash
cd frontend
pnpm dlx shadcn@latest add alert-dialog
```

- [ ] **Step 2: Create the delete confirmation component**

Uses `useTransition` (not `useActionState`) because delete is a click-triggered
one-shot action, not a form submission. This avoids the onClick/form-action type
mismatch.

```tsx
"use client"

import { useTransition, type ReactNode } from "react"
import { toast } from "sonner"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"

import { deleteTimelineEvent } from "./timeline-actions"

type DeleteEventDialogProps = {
  eventId: string
  applicationId: string
  children: ReactNode
}

export function DeleteEventDialog({
  eventId,
  applicationId,
  children,
}: DeleteEventDialogProps) {
  const [isPending, startTransition] = useTransition()

  function handleDelete() {
    startTransition(async () => {
      const result = await deleteTimelineEvent(eventId, applicationId)
      if (result.ok) {
        toast.success("Event deleted")
      } else if (result.error) {
        toast.error(result.error)
      }
    })
  }

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>{children}</AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete this event?</AlertDialogTitle>
          <AlertDialogDescription>
            This can&apos;t be undone. The event will be permanently removed from the timeline.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={isPending}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isPending ? "Deleting…" : "Delete"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
```

- [ ] **Step 3: Verify lint + typecheck**

```bash
cd frontend
pnpm lint
pnpm typecheck
```

Expected: clean.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ui/alert-dialog.tsx frontend/src/features/applications/delete-event-dialog.tsx
git commit -m "feat(frontend): delete event confirmation dialog (AlertDialog)"
```

---

## Task 13: Update timeline component to use buildTimeline

**Files:**
- Modify: `frontend/src/features/applications/application-timeline.tsx`

- [ ] **Step 1: Replace the component with a render-only version**

Replace the entire file with:

```tsx
import { Trash2 } from "lucide-react"

import type { Application, StageHistory, TimelineEvent } from "@/types"
import { cn } from "@/utils/cn"
import { buildTimeline, type TimelineEntry } from "@/utils/timeline"
import { Button } from "@/components/ui/button"
import { DeleteEventDialog } from "./delete-event-dialog"

type ApplicationTimelineProps = {
  application: Application
  history: StageHistory[]
  events: TimelineEvent[]
}

/**
 * Vertical timeline for an application workspace.
 *
 * Renders from `buildTimeline()` — all merge + normalization logic lives in
 * `utils/timeline.ts`. Reads oldest-first so it tells a narrative.
 */
export function ApplicationTimeline({
  application,
  history,
  events,
}: ApplicationTimelineProps) {
  const entries = buildTimeline(application, history, events)

  if (entries.length === 0) {
    return (
      <p className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
        No activity yet.
      </p>
    )
  }

  return (
    <ol className="relative space-y-1">
      <span
        aria-hidden
        className="pointer-events-none absolute bottom-3 left-[15px] top-3 w-px bg-border"
      />
      {entries.map((entry) => (
        <TimelineRow
          key={entry.id}
          entry={entry}
          applicationId={application.id}
        />
      ))}
    </ol>
  )
}

function TimelineRow({
  entry,
  applicationId,
}: {
  entry: TimelineEntry
  applicationId: string
}) {
  const isMilestone = entry.importance === "MILESTONE"
  const isImportant = entry.importance === "IMPORTANT" || isMilestone

  return (
    <li className="group relative flex gap-4 pb-6 last:pb-0">
      <span
        aria-hidden
        className={cn(
          "z-10 mt-1 flex shrink-0 items-center justify-center rounded-full border",
          isMilestone ? "size-9" : "size-8",
          entry.tone === "primary" && "border-primary/30 bg-primary/10 text-primary",
          entry.tone === "success" && "border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
          entry.tone === "danger" && "border-destructive/30 bg-destructive/10 text-destructive",
          entry.tone === "muted" && "border-border bg-background text-muted-foreground",
        )}
      >
        <entry.icon className={cn(isMilestone ? "size-4.5" : "size-4")} />
      </span>
      <div className="min-w-0 flex-1 pt-0.5">
        <div className="flex flex-wrap items-baseline justify-between gap-x-3">
          <p
            className={cn(
              "text-sm text-foreground",
              isImportant && "font-semibold",
            )}
          >
            {entry.title}
          </p>
          <time className="font-mono text-xs text-muted-foreground">
            {entry.atLabel}
          </time>
        </div>
        {entry.subtitle && (
          <p className="mt-0.5 text-sm text-muted-foreground">{entry.subtitle}</p>
        )}
        {entry.note && (
          <p className="mt-2 rounded-md border border-border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
            {entry.note}
          </p>
        )}
        {entry.kind === "event" && (
          <div className="mt-2 opacity-0 transition-opacity group-hover:opacity-100">
            <DeleteEventDialog
              eventId={entry.id}
              applicationId={applicationId}
            >
              <Button variant="ghost" size="sm" className="h-7 text-xs text-muted-foreground">
                <Trash2 className="mr-1 size-3" />
                Delete
              </Button>
            </DeleteEventDialog>
          </div>
        )}
      </div>
    </li>
  )
}
```

- [ ] **Step 2: Verify typecheck**

```bash
cd frontend
pnpm typecheck
```

Expected: clean (may need the page.tsx update in Task 14 to pass if it's imported there).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/applications/application-timeline.tsx
git commit -m "refactor(frontend): timeline renders from buildTimeline, adds delete-on-hover"
```

---

## Task 14: Wire up the workspace page

**Files:**
- Modify: `frontend/src/app/(app)/applications/[id]/page.tsx`

- [ ] **Step 1: Add the events fetch and pass to components**

Add `listTimelineEvents` to the imports from `@/services/api-client` (line 5):

```tsx
import { getApplication, listDocuments, listStageHistory, listTimelineEvents } from "@/services/api-client"
```

Add `TimelineEvent` to the type imports (line 6):

```tsx
import type { Application, Document, StageHistory, TimelineEvent } from "@/types"
```

Add the `events` variable alongside `documents` and `history` (after line 32):

```tsx
  let events: TimelineEvent[] = []
```

Add the fetch inside the `if (application)` block (after the documents try/catch, around line 53):

```tsx
    try {
      events = await listTimelineEvents(id)
    } catch {
      // empty events is fine
    }
```

Update the Timeline section to pass `events` and add the AddEventForm. Replace the section `<section className="space-y-4">` block (lines 128-136) with:

```tsx
        <section className="space-y-4">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <History className="size-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                Timeline
              </h2>
            </div>
            <AddEventForm
              applicationId={application.id}
              trigger={
                <Button variant="outline" size="sm">
                  <Plus className="mr-1.5 h-4 w-4" />
                  Add Event
                </Button>
              }
            />
          </div>
          <ApplicationTimeline application={application} history={history} events={events} />
        </section>
```

Add the imports for `AddEventForm` and `Plus` at the top of the file:

```tsx
import { ArrowLeft, ExternalLink, History, Pencil, Plus } from "lucide-react"
```

```tsx
import { AddEventForm } from "@/features/applications/add-event-form"
```

- [ ] **Step 2: Verify lint + typecheck + build**

```bash
cd frontend
pnpm lint
pnpm typecheck
pnpm build
```

Expected: all clean, build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/\(app\)/applications/\[id\]/page.tsx
git commit -m "feat(frontend): wire timeline events into application workspace"
```

---

## Task 15: Full verification + backend lint

- [ ] **Step 1: Backend full check**

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run --extra dev pytest -q
```

Expected: all clean, all tests pass (DB tests pass if Postgres running; skip otherwise).

- [ ] **Step 2: Frontend full check**

```bash
cd frontend
pnpm lint
pnpm typecheck
pnpm build
```

Expected: all clean.

- [ ] **Step 3: Fix any issues found, then commit**

If any issues were found and fixed, commit them. Otherwise, no commit needed.

---

## Self-Review Checklist

**Spec coverage:**
- [x] event_type native enum — Task 1 (migration), Task 2 (model)
- [x] importance — Task 1, Task 2
- [x] follow_up_date (nullable) — Task 1, Task 2
- [x] source column — Task 1, Task 2
- [x] title → summary rename — Task 1, Task 2
- [x] Repository with occurred_at ordering — Task 4
- [x] Service with application ownership check — Task 5
- [x] Rejection reason sync on REJECTED — Task 5, Task 7 (test)
- [x] Routes (GET/POST/DELETE) — Task 6
- [x] Centralized metadata (utils/timeline.ts) — Task 9
- [x] buildTimeline merge logic — Task 9
- [x] Server Actions — Task 10
- [x] Add Event form — Task 11
- [x] Delete confirmation (AlertDialog) — Task 12
- [x] Component renders from buildTimeline — Task 13
- [x] Workspace page integration — Task 14
- [x] Full verification — Task 15
