# D2 + D3 Document Version Links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Link applications to the resume and cover-letter **versions** used for them (two nullable FKs → root documents, `SET NULL`), with form pickers, embedded refs on reads, and a per-version performance analytics endpoint.

**Architecture:** Additive migration `0012` on `applications`; service-level link validation (404 unknown/foreign, 422 wrong type/non-root) reusing the user-scoped `DocumentRepository`; analytics reuses the stage-entered semantics from `summary` partitioned by the FK; frontend threads server-fetched document options into the existing form dialog.

**Tech Stack:** FastAPI + SQLAlchemy 2 (async) + Alembic + Pydantic v2; Next.js 15 App Router + React 19 + shadcn/ui.

**Spec:** `docs/superpowers/specs/2026-10-13-document-links-design.md`

**Test environment note:** backend tests auto-skip when Postgres is unreachable (`tests/conftest.py` `require_db`). Full verification: `DATABASE_URL=postgresql+asyncpg://careeros:careeros@localhost:5433/careeros uv run --extra dev pytest` from `backend/`. If Docker Desktop is down, start it first (the db container publishes host port 5433).

---

## File Structure

**Backend**
- Create: `backend/alembic/versions/0012_application_document_links.py` — schema change
- Modify: `backend/src/careeros_api/models/application.py` — 2 columns, 2 relationships, 2 indexes
- Modify: `backend/src/careeros_api/errors.py` — `UnprocessableError` (422)
- Modify: `backend/src/careeros_api/schemas/application.py` — `DocumentVersionRef` + fields
- Modify: `backend/src/careeros_api/services/application.py` — link validation on create/update
- Modify: `backend/src/careeros_api/repositories/application.py` — eager-load refs (3 places)
- Modify: `backend/src/careeros_api/schemas/analytics.py` — `DocumentPerformanceItem/DocumentPerformance`
- Modify: `backend/src/careeros_api/repositories/analytics.py` — `document_performance` queries
- Modify: `backend/src/careeros_api/services/analytics.py` — `document_performance`
- Modify: `backend/src/careeros_api/api/v1/routes/analytics.py` — `GET /document-performance`
- Modify: `backend/tests/test_applications.py` — link tests
- Modify: `backend/tests/test_analytics.py` — performance tests

**Frontend**
- Modify: `frontend/src/types/index.ts` — `DocumentVersionRef`, `DocumentPerformance*`, `Application` fields
- Modify: `frontend/src/services/api-client.ts` — `getDocumentPerformance`
- Modify: `frontend/src/features/applications/actions.ts` — `linkValue` + payload fields
- Modify: `frontend/src/features/applications/application-form.tsx` — two pickers
- Modify: `frontend/src/features/applications/applications-table.tsx` — thread options
- Modify: `frontend/src/app/(app)/applications/page.tsx` — fetch options
- Modify: `frontend/src/app/(app)/applications/[id]/page.tsx` — fetch + pass options
- Modify: `frontend/src/features/applications/application-details.tsx` — display links

**Docs**
- Modify: `docs/API.md`

---

### Task 1: Migration + ORM columns/relationships

**Files:**
- Create: `backend/alembic/versions/0012_application_document_links.py`
- Modify: `backend/src/careeros_api/models/application.py`

- [ ] **Step 1: Write the migration**

Create `backend/alembic/versions/0012_application_document_links.py`:

```python
"""Application → document version links (D2 + D3).

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-13

Links an application to the resume / cover-letter document group used for
it. The FK targets a group ROOT (service-enforced); file revisions under the
root do not change the link. Deleting a document nulls the link (SET NULL).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _add_link(column: str) -> None:
    op.add_column(
        "applications",
        sa.Column(column, postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        f"fk_applications_{column}",
        "applications",
        "documents",
        [column],
        ["id"],
        ondelete="SET NULL",
    )
    # Partial index: analytics groups by the FK over linked rows only.
    op.create_index(
        f"ix_applications_{column}",
        "applications",
        [column],
        postgresql_where=sa.text(f"{column} IS NOT NULL"),
    )


def upgrade() -> None:
    _add_link("resume_version_id")
    _add_link("cover_letter_version_id")


def downgrade() -> None:
    for column in ("resume_version_id", "cover_letter_version_id"):
        op.drop_index(f"ix_applications_{column}", table_name="applications")
        op.drop_constraint(f"fk_applications_{column}", "applications", type_="foreignkey")
        op.drop_column("applications", column)
```

- [ ] **Step 2: Update the ORM model**

In `backend/src/careeros_api/models/application.py`:

Add to imports:

```python
from careeros_api.models.document import Document
```

Add to `__table_args__` (after the existing `ix_applications_user_id_created_at_id` entry):

```python
        Index(
            "ix_applications_resume_version_id",
            "resume_version_id",
            postgresql_where=text("resume_version_id IS NOT NULL"),
        ),
        Index(
            "ix_applications_cover_letter_version_id",
            "cover_letter_version_id",
            postgresql_where=text("cover_letter_version_id IS NOT NULL"),
        ),
```

Add the columns after `rejection_reason_category` (around line 91):

```python
    # D2/D3: document group (root) used for this application. SET NULL when
    # the document is deleted; service layer enforces root + type.
    resume_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    cover_letter_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )
```

Add the relationships after the `tags` relationship:

```python
    resume_version: Mapped[Document | None] = relationship(
        Document,
        foreign_keys=[resume_version_id],
        uselist=False,
    )
    cover_letter_version: Mapped[Document | None] = relationship(
        Document,
        foreign_keys=[cover_letter_version_id],
        uselist=False,
    )
```

(`Document` has no import of `Application`, so there is no circular import.)

- [ ] **Step 3: Verify the migration applies both ways**

Run from `backend/` with the DB up:

```bash
export DATABASE_URL=postgresql+asyncpg://careeros:careeros@localhost:5433/careeros
uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head
uv run alembic current
```

Expected: no errors; final line shows `0012 (head)`. If the DB is unreachable, verify in Task 5's full run instead.

- [ ] **Step 4: Commit**

```bash
git add backend/alembic/versions/0012_application_document_links.py backend/src/careeros_api/models/application.py
git commit -m "feat(db): application document version links — set-null fks, partial indexes"
```

---

### Task 2: UnprocessableError + application schemas

**Files:**
- Modify: `backend/src/careeros_api/errors.py`
- Modify: `backend/src/careeros_api/schemas/application.py`

- [ ] **Step 1: Add `UnprocessableError` to errors.py**

In `backend/src/careeros_api/errors.py`, after `InvalidCursorError`:

```python
class UnprocessableError(Exception):
    """Raised when a request is semantically invalid (maps to HTTP 422)."""
```

And inside `register_exception_handlers`, after the `InvalidCursorError` handler:

```python
    @app.exception_handler(UnprocessableError)
    async def handle_unprocessable_error(_: Request, exc: UnprocessableError) -> JSONResponse:
        return problem(
            422,
            "Validation Error",
            str(exc) or "The request is semantically invalid.",
        )
```

- [ ] **Step 2: Extend the application schemas**

In `backend/src/careeros_api/schemas/application.py`:

Add above `ApplicationBase`:

```python
class DocumentVersionRef(BaseModel):
    """Minimal document-group reference embedded on application reads."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    version_label: str | None = None
```

In `ApplicationCreate`, after `tags`:

```python
    # Document group (root) ids used for this application. Validated by the
    # service: must be a caller-owned root of the matching type.
    resume_version_id: uuid.UUID | None = None
    cover_letter_version_id: uuid.UUID | None = None
```

In `ApplicationUpdate`, after `tags`:

```python
    # Explicit ``null`` clears the link; omitting the field leaves it
    # untouched (exclude_unset semantics, same as every other field here).
    resume_version_id: uuid.UUID | None = None
    cover_letter_version_id: uuid.UUID | None = None
```

In `ApplicationRead`, after `rejection_reason_category`:

```python
    resume_version_id: uuid.UUID | None = None
    cover_letter_version_id: uuid.UUID | None = None
    resume_version: DocumentVersionRef | None = None
    cover_letter_version: DocumentVersionRef | None = None
```

- [ ] **Step 3: Lint + typecheck**

Run: `cd backend && uv run ruff check . && uv run ruff format . && uv run mypy src`
Expected: clean (fake_data.py's 4 pre-existing errors aside).

- [ ] **Step 4: Commit**

```bash
git add backend/src/careeros_api/errors.py backend/src/careeros_api/schemas/application.py
git commit -m "feat(api): document version ref schema + 422 unprocessable error"
```

---

### Task 3: Service validation + repository eager-loading

**Files:**
- Modify: `backend/src/careeros_api/services/application.py`
- Modify: `backend/src/careeros_api/repositories/application.py`

- [ ] **Step 1: Add the validation helper and wire it into create/update**

In `backend/src/careeros_api/services/application.py`:

Extend imports:

```python
from careeros_api.errors import NotFoundError, UnprocessableError
from careeros_api.models.document import Document
from careeros_api.repositories.document import DocumentRepository
```

Add the helper above `create_application`:

```python
async def _validated_document_link(
    session: AsyncSession,
    user: User,
    document_id: uuid.UUID,
    *,
    expected_type: str,
    field: str,
) -> None:
    """Ensure ``document_id`` is a caller-owned root of ``expected_type``.

    Unknown or foreign ids raise ``NotFoundError`` (consistent with
    ``company_id`` handling — existence is never leaked); owned-but-wrong
    targets raise ``UnprocessableError`` (422).
    """
    repo = DocumentRepository(session)
    document = await repo.get(user.id, document_id)
    if document is None:
        raise NotFoundError(f"Document {document_id} not found")
    if document.parent_document_id is not None:
        raise UnprocessableError(f"{field} must reference a root document, not a revision")
    if document.type != expected_type:
        raise UnprocessableError(f"{field} must reference a {expected_type} document")
```

In `create_application`, after the company resolution block and before `repo = ApplicationRepository(session)`:

```python
    if data.resume_version_id is not None:
        await _validated_document_link(
            session, user, data.resume_version_id, expected_type="resume", field="resume_version_id"
        )
    if data.cover_letter_version_id is not None:
        await _validated_document_link(
            session,
            user,
            data.cover_letter_version_id,
            expected_type="cover_letter",
            field="cover_letter_version_id",
        )
```

In `update_application` (after `if application is None: raise ...`), add:

```python
    if (
        "resume_version_id" in data.model_fields_set
        and data.resume_version_id is not None
    ):
        await _validated_document_link(
            session, user, data.resume_version_id, expected_type="resume", field="resume_version_id"
        )
    if (
        "cover_letter_version_id" in data.model_fields_set
        and data.cover_letter_version_id is not None
    ):
        await _validated_document_link(
            session,
            user,
            data.cover_letter_version_id,
            expected_type="cover_letter",
            field="cover_letter_version_id",
        )
```

(`model_fields_set` distinguishes "explicitly provided" from "default None", so validation only runs when the client sent a non-null link.)

- [ ] **Step 2: Pass the fields through the repository**

In `backend/src/careeros_api/repositories/application.py`:

In `create`, the payload dump is `data.model_dump(exclude={"company_id", "company_name", "tags"})` — the two new columns flow into the `Application(...)` constructor automatically because they are now ORM columns. **No change needed** in `create`.

In `update`, the dump uses `exclude_unset=True` — explicit nulls clear, absent fields untouched. **No change needed.**

- [ ] **Step 3: Eager-load the refs**

In `backend/src/careeros_api/repositories/application.py` there are three option blocks loading `selectinload(Application.company), selectinload(Application.current_stage), selectinload(Application.tags)` (in `list`, `get`, and `reload`). Add to **each**:

```python
                selectinload(Application.resume_version),
                selectinload(Application.cover_letter_version),
```

- [ ] **Step 4: Typecheck + lint**

Run: `cd backend && uv run mypy src && uv run ruff check . && uv run ruff format .`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add backend/src/careeros_api/services/application.py backend/src/careeros_api/repositories/application.py
git commit -m "feat(api): validated resume/cover-letter links on applications"
```

---

### Task 4: Document performance analytics

**Files:**
- Modify: `backend/src/careeros_api/schemas/analytics.py`
- Modify: `backend/src/careeros_api/repositories/analytics.py`
- Modify: `backend/src/careeros_api/services/analytics.py`
- Modify: `backend/src/careeros_api/api/v1/routes/analytics.py`

- [ ] **Step 1: Schemas**

In `backend/src/careeros_api/schemas/analytics.py`, append:

```python
DocumentPerformanceType = Literal["resume", "cover_letter"]


class DocumentPerformanceItem(BaseModel):
    """Per-document-group performance for one link type."""

    document_id: uuid.UUID
    name: str
    version_label: str | None = None
    applications: int
    interviews: int
    offers: int
    response_rate: float


class DocumentPerformance(BaseModel):
    """Resume/cover-letter performance rows, ordered by applications DESC."""

    generated_at: datetime
    type: DocumentPerformanceType
    items: list[DocumentPerformanceItem]
```

- [ ] **Step 2: Repository queries**

In `backend/src/careeros_api/repositories/analytics.py`:

Extend imports:

```python
from careeros_api.models.application import Application
from careeros_api.models.application_stage_history import ApplicationStageHistory
from careeros_api.models.document import Document
from careeros_api.models.pipeline_stage import PipelineStage
```

(`Application`/`ApplicationStageHistory`/`PipelineStage` are already imported — keep them once.)

Append:

```python
async def document_performance(
    session: AsyncSession, user_id: uuid.UUID, *, doc_type: str
) -> tuple[dict[uuid.UUID, int], dict[uuid.UUID, dict[str, int]], list[Document]]:
    """Aggregates for the document-performance endpoint.

    Returns ``(applications_per_doc, entered_counts_per_doc, documents)``:

    * ``applications_per_doc`` — live (not deleted) applications per linked
      document id.
    * ``entered_counts_per_doc`` — ``{doc_id: {"interview": n, "offer": n}}``
      counting DISTINCT applications that ever entered a stage named
      Interview/Offer (case-insensitive), partitioned by the link FK. Mirrors
      the semantics of :func:`stage_entered_counts`.
    * ``documents`` — the linked root documents of ``doc_type`` (metadata).
    """
    fk = (
        Application.resume_version_id
        if doc_type == "resume"
        else Application.cover_letter_version_id
    )

    apps_stmt = (
        select(fk.label("doc_id"), func.count().label("apps"))
        .where(
            Application.user_id == user_id,
            Application.deleted_at.is_(None),
            fk.is_not(None),
        )
        .group_by(fk)
    )
    apps_per_doc: dict[uuid.UUID, int] = {
        row.doc_id: int(row.apps) for row in (await session.execute(apps_stmt)).all()
    }

    stage_name = func.lower(PipelineStage.name)
    entered_stmt = (
        select(
            fk.label("doc_id"),
            stage_name.label("stage"),
            func.count(ApplicationStageHistory.application_id.distinct()).label("apps"),
        )
        .join(Application, Application.id == ApplicationStageHistory.application_id)
        .join(PipelineStage, PipelineStage.id == ApplicationStageHistory.to_stage_id)
        .where(
            Application.user_id == user_id,
            Application.deleted_at.is_(None),
            fk.is_not(None),
            stage_name.in_(("interview", "offer")),
        )
        .group_by(fk, stage_name)
    )
    entered_per_doc: dict[uuid.UUID, dict[str, int]] = {}
    for row in (await session.execute(entered_stmt)).all():
        entered_per_doc.setdefault(row.doc_id, {})[row.stage] = int(row.apps)

    docs_stmt = select(Document).where(
        Document.user_id == user_id,
        Document.parent_document_id.is_(None),
        Document.type == doc_type,
        Document.id.in_(select(apps_stmt.subquery().c.doc_id)),
    )
    docs = list((await session.execute(docs_stmt)).scalars().all())

    return apps_per_doc, entered_per_doc, docs
```

- [ ] **Step 3: Service**

In `backend/src/careeros_api/services/analytics.py`, extend the schema import with `DocumentPerformance, DocumentPerformanceItem`, and the repo import is already `analytics_repo`. Append:

```python
async def document_performance(
    session: AsyncSession,
    user: User,
    *,
    doc_type: str,
) -> DocumentPerformance:
    """Per-document-group application/interview/offer rates for ``doc_type``.

    Rows are ordered by application count DESC; documents with no linked
    applications are omitted (they would be zero-noise).
    """
    apps_per_doc, entered_per_doc, docs = await analytics_repo.document_performance(
        session, user.id, doc_type=doc_type
    )
    items: list[DocumentPerformanceItem] = []
    for doc in docs:
        n_apps = apps_per_doc.get(doc.id, 0)
        stage_counts = entered_per_doc.get(doc.id, {})
        interviews = stage_counts.get("interview", 0)
        offers = stage_counts.get("offer", 0)
        rate = (interviews + offers) / n_apps if n_apps else 0.0
        items.append(
            DocumentPerformanceItem(
                document_id=doc.id,
                name=doc.name,
                version_label=doc.version_label,
                applications=n_apps,
                interviews=interviews,
                offers=offers,
                response_rate=round(rate, 3),
            )
        )
    items.sort(key=lambda item: item.applications, reverse=True)
    return DocumentPerformance(
        generated_at=datetime.now(tz=UTC),
        type=doc_type,
        items=items,
    )
```

- [ ] **Step 4: Route**

In `backend/src/careeros_api/api/v1/routes/analytics.py`, mirror the file's existing imports/deps (it already imports `SessionDep`/`CurrentUserDep` equivalents and the service). Add `Query` to the fastapi import if missing, extend the schema import with `DocumentPerformance`, and add:

```python
@router.get("/document-performance", response_model=DocumentPerformance)
async def get_document_performance(
    session: SessionDep,
    current_user: CurrentUserDep,
    type: DocumentPerformanceType = Query("resume"),
) -> DocumentPerformance:
    """Per-document-group performance for the given document type."""
    return await analytics_service.document_performance(session, current_user, doc_type=type)
```

Import `DocumentPerformanceType` alongside `DocumentPerformance` from the analytics schemas. An invalid `type` value is rejected by the Literal as 422 automatically.

- [ ] **Step 5: Typecheck + lint + import smoke**

Run: `cd backend && uv run mypy src && uv run ruff check . && uv run ruff format .`
Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add backend/src/careeros_api/schemas/analytics.py backend/src/careeros_api/repositories/analytics.py backend/src/careeros_api/services/analytics.py backend/src/careeros_api/api/v1/routes/analytics.py
git commit -m "feat(api): document performance analytics endpoint"
```

---

### Task 5: Backend tests

**Files:**
- Modify: `backend/tests/test_applications.py`
- Modify: `backend/tests/test_analytics.py`

- [ ] **Step 1: Application link tests**

Append to `backend/tests/test_applications.py` (reuse its existing `_company`/`_application` helpers; check their exact names first and adapt):

```python
async def _document(
    client: AsyncClient, headers: dict[str, str], doc_type: str = "resume", name: str = "cv.pdf"
) -> str:
    created = await client.post(
        "/api/v1/documents",
        headers=headers,
        json={"type": doc_type, "name": name, "mime_type": "application/pdf"},
    )
    assert created.status_code == 201, created.text
    return cast(str, created.json()["id"])


async def test_create_application_with_document_links(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _company(client, headers, "Link Co")
    resume_id = await _document(client, headers, "resume", "cv.pdf")
    cl_id = await _document(client, headers, "cover_letter", "cl.pdf")

    created = await client.post(
        "/api/v1/applications",
        headers=headers,
        json={
            "company_id": company_id,
            "role_title": "Eng",
            "resume_version_id": resume_id,
            "cover_letter_version_id": cl_id,
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["resume_version_id"] == resume_id
    assert body["cover_letter_version_id"] == cl_id
    assert body["resume_version"]["name"] == "cv.pdf"
    assert body["cover_letter_version"]["name"] == "cl.pdf"


async def test_link_to_foreign_document_is_404(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    owner, intruder = auth(), auth()
    company_id = await _company(client, intruder, "Owner Co")
    resume_id = await _document(client, owner, "resume", "owner-cv.pdf")

    created = await client.post(
        "/api/v1/applications",
        headers=intruder,
        json={
            "company_id": company_id,
            "role_title": "Eng",
            "resume_version_id": resume_id,
        },
    )
    assert created.status_code == 404


async def test_link_to_wrong_type_is_422(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _company(client, headers, "Type Co")
    cl_id = await _document(client, headers, "cover_letter", "cl.pdf")

    created = await client.post(
        "/api/v1/applications",
        headers=headers,
        json={
            "company_id": company_id,
            "role_title": "Eng",
            "resume_version_id": cl_id,  # cover letter linked as resume
        },
    )
    assert created.status_code == 422


async def test_link_to_revision_is_422(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _company(client, headers, "Rev Co")
    resume_id = await _document(client, headers, "resume", "cv.pdf")
    revision = await client.post(
        f"/api/v1/documents/{resume_id}/revisions",
        headers=headers,
        json={"name": "cv v2.pdf"},
    )
    assert revision.status_code == 201, revision.text

    created = await client.post(
        "/api/v1/applications",
        headers=headers,
        json={
            "company_id": company_id,
            "role_title": "Eng",
            "resume_version_id": revision.json()["id"],
        },
    )
    assert created.status_code == 422


async def test_update_link_change_and_clear(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _company(client, headers, "Upd Co")
    application_id = await _application(client, headers, company_id)
    resume_a = await _document(client, headers, "resume", "a.pdf")
    resume_b = await _document(client, headers, "resume", "b.pdf")

    linked = await client.patch(
        f"/api/v1/applications/{application_id}",
        headers=headers,
        json={"resume_version_id": resume_a},
    )
    assert linked.status_code == 200, linked.text
    assert linked.json()["resume_version_id"] == resume_a

    changed = await client.patch(
        f"/api/v1/applications/{application_id}",
        headers=headers,
        json={"resume_version_id": resume_b},
    )
    assert changed.json()["resume_version_id"] == resume_b

    cleared = await client.patch(
        f"/api/v1/applications/{application_id}",
        headers=headers,
        json={"resume_version_id": None},
    )
    assert cleared.json()["resume_version_id"] is None
    assert cleared.json()["resume_version"] is None


async def test_deleting_linked_document_nulls_link(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    company_id = await _company(client, headers, "Del Co")
    resume_id = await _document(client, headers, "resume", "cv.pdf")
    application_id = await _application(client, headers, company_id)
    await client.patch(
        f"/api/v1/applications/{application_id}",
        headers=headers,
        json={"resume_version_id": resume_id},
    )

    deleted = await client.delete(f"/api/v1/documents/{resume_id}", headers=headers)
    assert deleted.status_code == 204

    read = await client.get(f"/api/v1/applications/{application_id}", headers=headers)
    assert read.status_code == 200
    assert read.json()["resume_version_id"] is None
    assert read.json()["resume_version"] is None
```

- [ ] **Step 2: Analytics tests**

Append to `backend/tests/test_analytics.py` (reuse/mirror its existing helpers for creating applications and stages; if it lacks a move helper, use the one below):

```python
async def _move_to_stage(
    client: AsyncClient, headers: dict[str, str], application_id: str, stage_name: str
) -> None:
    stages = (await client.get("/api/v1/pipeline-stages", headers=headers)).json()
    stage_id = next(s["id"] for s in stages if s["name"].lower() == stage_name.lower())
    response = await client.post(
        f"/api/v1/applications/{application_id}/move",
        headers=headers,
        json={"to_stage_id": stage_id},
    )
    assert response.status_code == 200, response.text


async def test_document_performance_counts(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    resume_a = (await client.post(
        "/api/v1/documents", headers=headers,
        json={"type": "resume", "name": "a.pdf"},
    )).json()["id"]
    resume_b = (await client.post(
        "/api/v1/documents", headers=headers,
        json={"type": "resume", "name": "b.pdf"},
    )).json()["id"]
    cl_id = (await client.post(
        "/api/v1/documents", headers=headers,
        json={"type": "cover_letter", "name": "cl.pdf"},
    )).json()["id"]

    company_id = (await client.post(
        "/api/v1/companies", headers=headers, json={"name": "Perf Co"},
    )).json()["id"]

    async def _app(link_key: str, link_id: str) -> str:
        created = await client.post(
            "/api/v1/applications",
            headers=headers,
            json={"company_id": company_id, "role_title": "Eng", link_key: link_id},
        )
        assert created.status_code == 201, created.text
        return cast(str, created.json()["id"])

    # a: one offer app + one plain app; b: one interview app; unlinked: 1.
    offer_app = await _app("resume_version_id", resume_a)
    plain_app = await _app("resume_version_id", resume_a)
    interview_app = await _app("resume_version_id", resume_b)
    await _app("cover_letter_version_id", cl_id)

    await _move_to_stage(client, headers, offer_app, "Offer")
    await _move_to_stage(client, headers, interview_app, "Interview")

    performance = await client.get(
        "/api/v1/analytics/document-performance?type=resume", headers=headers
    )
    assert performance.status_code == 200, performance.text
    body = performance.json()
    assert body["type"] == "resume"

    by_id = {item["document_id"]: item for item in body["items"]}
    assert set(by_id) == {resume_a, resume_b}  # unlinked + cover letter excluded
    a_row = by_id[resume_a]
    assert a_row["applications"] == 2
    assert a_row["interviews"] == 0
    assert a_row["offers"] == 1
    assert a_row["response_rate"] == 0.5
    b_row = by_id[resume_b]
    assert b_row["applications"] == 1
    assert b_row["interviews"] == 1
    assert b_row["offers"] == 0
    assert b_row["response_rate"] == 1.0
    # Ordered by applications DESC → a (2) before b (1).
    assert body["items"][0]["document_id"] == resume_a

    cl_perf = await client.get(
        "/api/v1/analytics/document-performance?type=cover_letter", headers=headers
    )
    assert cl_perf.status_code == 200, cl_perf.text
    cl_items = cl_perf.json()["items"]
    assert len(cl_items) == 1
    assert cl_items[0]["document_id"] == cl_id
    assert cl_items[0]["applications"] == 1


async def test_document_performance_invalid_type_is_422(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    response = await client.get(
        "/api/v1/analytics/document-performance?type=visa", headers=auth()
    )
    assert response.status_code == 422
```

- [ ] **Step 3: Run the new tests**

Run: `cd backend && DATABASE_URL=postgresql+asyncpg://careeros:careeros@localhost:5433/careeros uv run --extra dev pytest tests/test_applications.py tests/test_analytics.py -v`

Expected: all PASS (or SKIPPED if the DB is down — start it first; every failure is a real bug to fix).

- [ ] **Step 4: Full backend gates**

Run: `cd backend && DATABASE_URL=postgresql+asyncpg://careeros:careeros@localhost:5433/careeros uv run --extra dev pytest && uv run ruff check . && uv run mypy src`

Expected: all green (fake_data.py's pre-existing mypy errors aside).

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_applications.py backend/tests/test_analytics.py
git commit -m "test(api): document links — validation, set-null, performance analytics"
```

---

### Task 6: Frontend types + api-client + actions

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/services/api-client.ts`
- Modify: `frontend/src/features/applications/actions.ts`

- [ ] **Step 1: Types**

In `frontend/src/types/index.ts`, add near `Document`:

```ts
/** Minimal document-group reference embedded on application reads. */
export interface DocumentVersionRef {
  id: string
  name: string
  version_label: string | null
}
```

Add to the `Application` interface (after `rejection_reason_category`):

```ts
  resume_version_id?: string | null
  cover_letter_version_id?: string | null
  resume_version?: DocumentVersionRef | null
  cover_letter_version?: DocumentVersionRef | null
```

Add the analytics response types:

```ts
/** One row of GET /analytics/document-performance. */
export interface DocumentPerformanceItem {
  document_id: string
  name: string
  version_label: string | null
  applications: number
  interviews: number
  offers: number
  response_rate: number
}

export interface DocumentPerformance {
  generated_at: string
  type: "resume" | "cover_letter"
  items: DocumentPerformanceItem[]
}
```

- [ ] **Step 2: API client**

In `frontend/src/services/api-client.ts` (import the new types in the type-import block):

```ts
/** Per-document-group application/interview/offer rates (D2/D3 analytics). */
export async function getDocumentPerformance(
  type: "resume" | "cover_letter",
): Promise<DocumentPerformance> {
  return apiFetch<DocumentPerformance>(`/analytics/document-performance?type=${type}`)
}
```

- [ ] **Step 3: Actions payload**

In `frontend/src/features/applications/actions.ts`, add next to `numberValue`:

```ts
/** "none"/"" → null (clear the link); a uuid → the link; absent → undefined. */
function linkValue(formData: FormData, key: string): string | null | undefined {
  const raw = formData.get(key)
  if (raw === null) return undefined
  const value = String(raw).trim()
  if (value === "" || value === "none") return null
  return value
}
```

In `buildApplicationPayload`, add:

```ts
    resume_version_id: linkValue(formData, "resume_version_id"),
    cover_letter_version_id: linkValue(formData, "cover_letter_version_id"),
```

(`compact()` strips `undefined`; `null` is sent explicitly so the backend's `exclude_unset` semantics clear the link.)

- [ ] **Step 4: Verify + commit**

Run: `cd frontend && pnpm typecheck && pnpm lint`

```bash
git add frontend/src/types/index.ts frontend/src/services/api-client.ts frontend/src/features/applications/actions.ts
git commit -m "feat(frontend): document link types, performance fetcher, form payload"
```

---

### Task 7: Form pickers + page threading + workspace display

**Files:**
- Modify: `frontend/src/features/applications/application-form.tsx`
- Modify: `frontend/src/features/applications/applications-table.tsx`
- Modify: `frontend/src/app/(app)/applications/page.tsx`
- Modify: `frontend/src/app/(app)/applications/[id]/page.tsx`
- Modify: `frontend/src/features/applications/application-details.tsx`

- [ ] **Step 1: Shared options type + form pickers**

In `frontend/src/features/applications/application-form.tsx`:

Import `Document` type. Add:

```ts
/** Document-group picker options, fetched server-side by the mounting page. */
export type DocumentLinkOptions = {
  resume: Document[]
  coverLetter: Document[]
}
```

Extend both prop types (`ApplicationFormProps` and `ApplicationFormFieldsProps`) with `documentOptions?: DocumentLinkOptions`, and pass it through `ApplicationForm` → `ApplicationFormFields`.

Inside `ApplicationFormFields`, after the salary grid and before the job description, add:

```tsx
        {(documentOptions?.resume.length || documentOptions?.coverLetter.length) && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {documentOptions && documentOptions.resume.length > 0 && (
              <div className="space-y-2">
                <Label htmlFor="resume_version_id">Resume used</Label>
                <Select
                  name="resume_version_id"
                  defaultValue={application?.resume_version_id ?? "none"}
                >
                  <SelectTrigger id="resume_version_id">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    {documentOptions.resume.map((doc) => (
                      <SelectItem key={doc.id} value={doc.id}>
                        {doc.version_label ? `${doc.name} — ${doc.version_label}` : doc.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            {documentOptions && documentOptions.coverLetter.length > 0 && (
              <div className="space-y-2">
                <Label htmlFor="cover_letter_version_id">Cover letter used</Label>
                <Select
                  name="cover_letter_version_id"
                  defaultValue={application?.cover_letter_version_id ?? "none"}
                >
                  <SelectTrigger id="cover_letter_version_id">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    {documentOptions.coverLetter.map((doc) => (
                      <SelectItem key={doc.id} value={doc.id}>
                        {doc.version_label ? `${doc.name} — ${doc.version_label}` : doc.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
        )}
```

Note: a group's representative `Document` (from the grouped list) carries `parent_document_id` — the picker value must be the **root** id. Use:

```ts
const rootId = doc.parent_document_id ?? doc.id
```

as the `<SelectItem value={rootId}>` (and same for `key`), since applications must link to roots.

- [ ] **Step 2: Thread options through the table**

In `frontend/src/features/applications/applications-table.tsx`: add `documentOptions?: DocumentLinkOptions` to `ApplicationsTableProps` and pass it to all four `<ApplicationForm>` usages.

- [ ] **Step 3: Fetch options in the pages**

In `frontend/src/app/(app)/applications/page.tsx` (import `listDocuments`):

```tsx
  // Document link options; failure is non-fatal (pickers just don't render).
  let documentOptions: DocumentLinkOptions = { resume: [], coverLetter: [] }
  try {
    const [resumes, coverLetters] = await Promise.all([
      listDocuments({ type: "resume", limit: 100 }),
      listDocuments({ type: "cover_letter", limit: 100 }),
    ])
    documentOptions = { resume: resumes.items, coverLetter: coverLetters.items }
  } catch {
    // pickers stay hidden
  }
```

Pass `documentOptions={documentOptions}` to `<ApplicationsTable>`.

In `frontend/src/app/(app)/applications/[id]/page.tsx`, add the same fetch (inside the existing authed try block, non-fatal on failure) and pass `documentOptions` to its `<ApplicationForm>`.

- [ ] **Step 4: Workspace display**

In `frontend/src/features/applications/application-details.tsx`, after the Source row:

```tsx
      {application.resume_version && (
        <DetailRow icon={FileText} label="Resume">
          {application.resume_version.version_label
            ? `${application.resume_version.name} — ${application.resume_version.version_label}`
            : application.resume_version.name}
        </DetailRow>
      )}
      {application.cover_letter_version && (
        <DetailRow icon={FileText} label="Cover letter">
          {application.cover_letter_version.version_label
            ? `${application.cover_letter_version.name} — ${application.cover_letter_version.version_label}`
            : application.cover_letter_version.name}
        </DetailRow>
      )}
```

- [ ] **Step 5: Verify + commit**

Run: `cd frontend && pnpm typecheck && pnpm lint && pnpm build`

```bash
git add frontend/src/features/applications frontend/src/app/(app)/applications
git commit -m "feat(frontend): resume/cover-letter pickers in application form"
```

---

### Task 8: API docs + full verification

**Files:**
- Modify: `docs/API.md`

- [ ] **Step 1: Document the API**

In `docs/API.md`:

1. Applications section — add the two fields to the create/update payload tables and note the validation (unknown/foreign → 404; wrong type or revision → 422; `null` clears).
2. Analytics section — add:

```markdown
#### GET /analytics/document-performance

**Purpose:** Per-document-group application/interview/offer rates for a link type.

**Query params:** `type` (`resume` | `cover_letter`, default `resume`).

Only document groups linked by ≥1 live application appear. `interviews`/`offers` count distinct applications that ever entered a stage named Interview/Offer; `response_rate = (interviews + offers) / applications`.

**Response `200`:**

```json
{
  "generated_at": "2026-10-13T12:00:00Z",
  "type": "resume",
  "items": [
    {
      "document_id": "70a1b2c3-…",
      "name": "resume_stripe_payments.pdf",
      "version_label": "v2 — Stripe focus",
      "applications": 12,
      "interviews": 3,
      "offers": 1,
      "response_rate": 0.333
    }
  ]
}
```
```

- [ ] **Step 2: Full verification sweep**

```bash
cd backend && DATABASE_URL=postgresql+asyncpg://careeros:careeros@localhost:5433/careeros uv run --extra dev pytest && uv run ruff check . && uv run ruff format --check . && uv run mypy src
cd ../frontend && pnpm lint && pnpm typecheck && pnpm build
cd .. && grep -n "ix_applications_resume_version_id\|ix_applications_cover_letter_version_id" backend/src/careeros_api/models/application.py backend/alembic/versions/0012_application_document_links.py
```

Expected: all green; index names identical in ORM and migration (no drift).

- [ ] **Step 3: Final commit**

```bash
git add docs/API.md
git commit -m "docs(api): document version links + performance endpoint"
```

---

## Self-Review (completed during planning)

- **Spec coverage:** §2 data model → Task 1; §3.1 schemas → Task 2; §3.2 validation → Task 3; §3.3 analytics → Task 4; §5 error table → Tasks 2/3/4; §6 testing → Task 5; §4 frontend → Tasks 6/7; §7 verification → Task 8.
- **Placeholders:** none — every step carries complete code or exact commands. The only "check first" instruction (helper names in existing test files) includes adaptable code.
- **Type consistency:** `DocumentVersionRef` defined identically in Task 2 (backend) and Task 6 (frontend); `DocumentLinkOptions` introduced in Task 7 and consumed in the same task; `linkValue`'s null/undefined contract matches the backend's `exclude_unset` semantics described in Task 2.
- **Known wrinkles:** the picker value uses `doc.parent_document_id ?? doc.id` (root id) because the grouped list returns representatives; `listDocuments` must accept `limit` (added in the D1 follow-up — already shipped).
