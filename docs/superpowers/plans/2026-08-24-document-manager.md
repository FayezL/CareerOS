# D1 Document Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn documents into grouped, versioned, categorised resources — 6 types, revision grouping via `parent_document_id`, a `/documents` Document Manager page, and DB-enforced "one latest per group" invariants.

**Architecture:** Additive migration (enum values + 3 columns + 4 indexes) on `documents`; a purpose-built grouped keyset query in the repository (two-step `DISTINCT ON`); a new nested revisions endpoint reusing the existing two-step upload flow; frontend gets a shared grouping helper used by both the new page and the workspace panel.

**Tech Stack:** FastAPI + SQLAlchemy 2 (async) + Alembic + Pydantic v2; Next.js 15 App Router + React 19 + shadcn/ui.

**Spec:** `docs/superpowers/specs/2026-08-24-document-manager-design.md`

**Test environment note:** backend tests auto-skip when Postgres is unreachable (`tests/conftest.py` `require_db`). For full verification run the suite where the DB is reachable, e.g. `docker compose up -d db` and `DATABASE_URL=postgresql+asyncpg://careeros:careeros@localhost:5433/careeros uv run --extra dev pytest tests/test_documents.py` from `backend/`. A skipped run still validates collection/imports.

---

## File Structure

**Backend**
- Create: `backend/alembic/versions/0011_document_versioning.py` — schema change
- Modify: `backend/src/careeros_api/models/document.py` — new columns + index parity
- Modify: `backend/src/careeros_api/schemas/document.py` — types, new fields, `DocumentRevisionCreate`
- Modify: `backend/src/careeros_api/repositories/document.py` — grouped list, next_version, revisions query
- Modify: `backend/src/careeros_api/services/document.py` — create/list/delete logic
- Modify: `backend/src/careeros_api/api/v1/routes/documents.py` — new routes + param
- Modify: `backend/tests/test_documents.py` — new tests
- Modify: `backend/src/careeros_api/errors.py` — only if `ConflictError` is missing (check first)

**Frontend**
- Modify: `frontend/src/types/index.ts` — Document type widening
- Modify: `frontend/src/services/api-client.ts` — list params + revisions fetchers
- Create: `frontend/src/features/documents/document-groups.ts` — grouping helper
- Create: `frontend/src/features/documents/document-groups.test.ts` — its tests
- Create: `frontend/src/app/(app)/documents/page.tsx` — Document Manager (server)
- Create: `frontend/src/app/(app)/documents/loading.tsx` — route loading state
- Create: `frontend/src/features/documents/document-manager.tsx` — client list UI
- Modify: `frontend/src/components/layout/sidebar.tsx` — nav entry
- Modify: `frontend/src/features/documents/documents-panel.tsx` — grouped workspace panel
- Modify: `frontend/src/features/documents/actions.ts` — revision create/delete actions

**Docs**
- Modify: `docs/API.md` — new endpoints + grouped list contract

---

### Task 1: Migration + ORM model

**Files:**
- Create: `backend/alembic/versions/0011_document_versioning.py`
- Modify: `backend/src/careeros_api/models/document.py`

- [ ] **Step 1: Write the migration**

Create `backend/alembic/versions/0011_document_versioning.py`:

```python
"""Document versioning: type expansion, grouping, version labels.

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-24

Downgrade drops the new columns/indexes but deliberately does NOT shrink
the document_type enum (Postgres cannot remove enum values without
recreating the type; extra unused values are harmless).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

GROUP_KEY = sa.text("COALESCE(parent_document_id, id)")


def upgrade() -> None:
    # ADD VALUE cannot run inside a transaction on some setups — use an
    # autocommit block so behaviour is deterministic.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE document_type ADD VALUE IF NOT EXISTS 'certificate'")
        op.execute("ALTER TYPE document_type ADD VALUE IF NOT EXISTS 'reference'")
        op.execute("ALTER TYPE document_type ADD VALUE IF NOT EXISTS 'visa'")

    op.add_column(
        "documents",
        sa.Column("parent_document_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_documents_parent_document_id",
        "documents",
        "documents",
        ["parent_document_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.add_column("documents", sa.Column("version_label", sa.String(255), nullable=True))
    op.add_column(
        "documents",
        sa.Column(
            "is_latest_version",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    op.create_index(
        "ix_documents_user_type_created_at",
        "documents",
        ["user_id", "type", sa.text("created_at DESC"), sa.text("id DESC")],
    )
    op.create_index("ix_documents_parent_document_id", "documents", ["parent_document_id"])
    op.create_index(
        "ix_documents_one_latest_per_group",
        "documents",
        [GROUP_KEY],
        unique=True,
        postgresql_where=sa.text("is_latest_version = true"),
    )
    op.create_index(
        "ix_documents_group_version",
        "documents",
        [GROUP_KEY, sa.text("version")],
        unique=True,
    )
    op.drop_index("ix_documents_user_id_type", table_name="documents")


def downgrade() -> None:
    op.create_index(
        "ix_documents_user_id_type",
        "documents",
        ["user_id", "type"],
    )
    op.drop_index("ix_documents_group_version", table_name="documents")
    op.drop_index("ix_documents_one_latest_per_group", table_name="documents")
    op.drop_index("ix_documents_parent_document_id", table_name="documents")
    op.drop_index("ix_documents_user_type_created_at", table_name="documents")
    op.drop_constraint("fk_documents_parent_document_id", "documents", type_="foreignkey")
    op.drop_column("documents", "is_latest_version")
    op.drop_column("documents", "version_label")
    op.drop_column("documents", "parent_document_id")
    # document_type enum is intentionally NOT shrunk (see module docstring).
```

- [ ] **Step 2: Update the ORM model**

In `backend/src/careeros_api/models/document.py`:

Replace the enum definition (lines 15-21) with:

```python
document_type = sa.Enum(
    "resume",
    "cover_letter",
    "certificate",
    "reference",
    "visa",
    "other",
    name="document_type",
    native_enum=True,
)
```

Replace `__table_args__` (lines 32-40) with:

```python
    __table_args__ = (
        Index(
            "ix_documents_user_type_created_at",
            "user_id",
            "type",
            text("created_at DESC"),
            text("id DESC"),
        ),
        Index("ix_documents_parent_document_id", "parent_document_id"),
        Index(
            "ix_documents_one_latest_per_group",
            text("COALESCE(parent_document_id, id)"),
            unique=True,
            postgresql_where=text("is_latest_version = true"),
        ),
        Index(
            "ix_documents_group_version",
            text("COALESCE(parent_document_id, id)"),
            text("version"),
            unique=True,
        ),
    )
```

Add the relationship + columns after the existing `application_id` column (keep `type`/`name`/etc. as-is):

```python
    parent_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
    )
```

And after `size_bytes` (before the existing `version` column):

```python
    version_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_latest_version: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=True,
        server_default=sa.text("true"),
    )
```

Note: `text` is already imported in the file (line 9).

- [ ] **Step 3: Verify the migration applies**

Run (DB reachable): `cd backend && uv run alembic upgrade head`
Expected: no output / success. Then `uv run alembic downgrade -1 && uv run alembic upgrade head` to prove both directions.
If DB unreachable locally, verify at Task 6's full run instead — do not skip writing the downgrade.

- [ ] **Step 4: Commit**

```bash
git add backend/alembic/versions/0011_document_versioning.py backend/src/careeros_api/models/document.py
git commit -m "feat(db): document versioning schema — grouping, labels, 6 types"
```

---

### Task 2: Pydantic schemas

**Files:**
- Modify: `backend/src/careeros_api/schemas/document.py`

- [ ] **Step 1: Update the schemas**

In `backend/src/careeros_api/schemas/document.py`:

Replace the `DocumentType` line (line 16) with:

```python
DocumentType = Literal["resume", "cover_letter", "certificate", "reference", "visa", "other"]
```

In `DocumentCreate`, add after `size_bytes`:

```python
    version_label: str | None = Field(default=None, max_length=255)
```

In `DocumentRead`, add after `version: int`:

```python
    parent_document_id: uuid.UUID | None = None
    version_label: str | None = None
    is_latest_version: bool = True
    # Populated only on grouped list reads; None on flat/single reads.
    revisions_count: int | None = None
```

Add a new model after `DocumentCreate`:

```python
class DocumentRevisionCreate(BaseModel):
    """Payload to create a new revision of an existing root document."""

    name: str = Field(..., min_length=1, max_length=255)
    mime_type: str | None = Field(default=None, max_length=255)
    size_bytes: int | None = Field(default=None, ge=0)
    version_label: str | None = Field(default=None, max_length=255)
```

- [ ] **Step 2: Verify import + validation**

Run:
```bash
cd backend && uv run python -c "
from pydantic import ValidationError
from careeros_api.schemas.document import DocumentType, DocumentRevisionCreate, DocumentRead
try:
    DocumentRevisionCreate(name='x' * 256)
    raise SystemExit('FAIL: long name accepted')
except ValidationError:
    pass
print('OK')
"
```
Expected: `OK`

- [ ] **Step 3: Lint + typecheck**

Run: `cd backend && uv run ruff check . && uv run ruff format . && uv run mypy src`
Expected: clean (fake_data.py's 4 pre-existing errors aside).

- [ ] **Step 4: Commit**

```bash
git add backend/src/careeros_api/schemas/document.py
git commit -m "feat(api): document schemas — 6 types, revision create, version fields"
```

---

### Task 3: Repository — grouped list, revisions, next_version

**Files:**
- Modify: `backend/src/careeros_api/repositories/document.py`

- [ ] **Step 1: Extend the repository**

Check `backend/src/careeros_api/errors.py` exports a `ConflictError` first (grep it); if missing, define usage in the service instead with whatever conflict error exists (do not invent a new error class without checking how routes map it — reuse the existing pattern).

In `backend/src/careeros_api/repositories/document.py`, update imports:

```python
import uuid
from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import ColumnExpressionArgument, select
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.models.document import Document
from careeros_api.repositories.base import BaseRepository, decode_cursor, encode_cursor
from careeros_api.schemas.document import DocumentCreate
```

Add to `DocumentRepository`:

```python
    @staticmethod
    def _group_key() -> sa.Label[Any]:
        """The group key: the root's id for every row in a group."""
        return sa.func.coalesce(Document.parent_document_id, Document.id).label("group_key")

    async def list_groups(
        self,
        user_id: uuid.UUID,
        *,
        limit: int,
        cursor: str | None = None,
        application_id: uuid.UUID | None = None,
        type_filter: str | None = None,
    ) -> tuple[Sequence[Document], str | None, dict[uuid.UUID, int]]:
        """One row per document group (the representative = newest row).

        Two-step query: the inner DISTINCT ON picks each group's newest row
        (DISTINCT ON requires the group key to lead its ORDER BY); the outer
        query applies keyset pagination on (created_at DESC, id DESC) over
        the representatives. Returns (rows, next_cursor, group_key -> count).
        """
        conditions: list[ColumnExpressionArgument[bool]] = [Document.user_id == user_id]
        if application_id is not None:
            conditions.append(Document.application_id == application_id)
        if type_filter is not None:
            conditions.append(Document.type == type_filter)

        group_key = self._group_key()
        inner = (
            select(Document.id.label("doc_id"))
            .where(*conditions)
            .distinct(group_key)
            .order_by(group_key, Document.created_at.desc(), Document.id.desc())
            .subquery()
        )

        stmt = select(Document).join(inner, Document.id == inner.c.doc_id)
        if cursor is not None:
            cursor_at, cursor_id = decode_cursor(cursor)
            stmt = stmt.where(
                (Document.created_at < cursor_at)
                | ((Document.created_at == cursor_at) & (Document.id < cursor_id))
            )
        stmt = stmt.order_by(Document.created_at.desc(), Document.id.desc()).limit(limit + 1)

        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())

        next_cursor: str | None = None
        if len(rows) > limit:
            last = rows[limit - 1]
            next_cursor = encode_cursor(last.created_at, last.id)
            rows = rows[:limit]

        counts: dict[uuid.UUID, int] = {}
        if rows:
            keys = [self._root_id_of(r) for r in rows]
            count_stmt = (
                select(group_key, sa.func.count().label("cnt"))
                .where(Document.user_id == user_id, group_key.in_(keys))
                .group_by(group_key)
            )
            count_result = await self.session.execute(count_stmt)
            counts = {row.group_key: int(row.cnt) for row in count_result}

        return rows, next_cursor, counts

    @staticmethod
    def _root_id_of(document: Document) -> uuid.UUID:
        return document.parent_document_id or document.id

    async def list_revisions(
        self, user_id: uuid.UUID, root_id: uuid.UUID
    ) -> Sequence[Document]:
        """All rows of a group (root + revisions), oldest first."""
        group_key = self._group_key()
        stmt = (
            select(Document)
            .where(Document.user_id == user_id, group_key == root_id)
            .order_by(Document.version.asc(), Document.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def next_version(self, user_id: uuid.UUID, root_id: uuid.UUID) -> int:
        """max(version) within the group + 1 (the race is resolved by the
        ix_documents_group_version unique index)."""
        group_key = self._group_key()
        stmt = select(sa.func.coalesce(sa.func.max(Document.version), 0)).where(
            Document.user_id == user_id, group_key == root_id
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one()) + 1
```

Add `from typing import Any` to the imports for the `sa.Label[Any]` annotation.

- [ ] **Step 2: Typecheck**

Run: `cd backend && uv run mypy src && uv run ruff check .`
Expected: clean.

- [ ] **Step 3: Commit**

```bash
git add backend/src/careeros_api/repositories/document.py
git commit -m "feat(db): grouped document queries — distinct-on pagination, revisions, next_version"
```

---

### Task 4: Service — create revision, grouped list, promote-on-delete

**Files:**
- Modify: `backend/src/careeros_api/services/document.py`

- [ ] **Step 1: Update imports**

In `backend/src/careeros_api/services/document.py` extend the schema import to include `DocumentRevisionCreate`, and import `ConflictError` from `careeros_api.errors` (adjust to the project's actual conflict error name found in Task 3).

- [ ] **Step 2: Change `list_documents` to grouped mode**

Replace the existing `list_documents` function with:

```python
async def list_documents(
    session: AsyncSession,
    user: User,
    *,
    limit: int,
    cursor: str | None,
    application_id: uuid.UUID | None,
    type_filter: str | None,
    include_revisions: bool = False,
) -> PageOut[DocumentRead]:
    """List the caller's documents.

    Grouped mode (default): one row per logical document (the newest row of
    each group) with ``revisions_count`` populated. Flat mode
    (``include_revisions=True``): every row, no counts.
    """
    repo = DocumentRepository(session)
    if include_revisions:
        items, next_cursor = await repo.list(
            user.id,
            limit=limit,
            cursor=cursor,
            application_id=application_id,
            type_filter=type_filter,
        )
        return PageOut(
            items=[DocumentRead.model_validate(d) for d in items], next_cursor=next_cursor
        )

    rows, next_cursor, counts = await repo.list_groups(
        user.id,
        limit=limit,
        cursor=cursor,
        application_id=application_id,
        type_filter=type_filter,
    )
    items = [
        DocumentRead.model_validate(
            d, update={"revisions_count": counts.get(repo._root_id_of(d), 1)}
        )
        for d in rows
    ]
    return PageOut(items=items, next_cursor=next_cursor)
```

- [ ] **Step 3: Add `create_document_revision`**

Add after `create_document`:

```python
async def create_document_revision(
    session: AsyncSession,
    user: User,
    root_id: uuid.UUID,
    data: DocumentRevisionCreate,
    storage: StorageClient,
) -> DocumentUploadTarget:
    """Create a revision of an existing root document.

    Ownership is enforced by loading the parent through the user-scoped
    repository (cross-user → 404). Revisions may only attach to roots.
    """
    repo = DocumentRepository(session)
    root = await repo.get(user.id, root_id)
    if root is None:
        raise NotFoundError(f"Document {root_id} not found")
    if root.parent_document_id is not None:
        raise ConflictError("Revisions can only be added to a root document")

    revision_id = uuid.uuid4()
    target: UploadTarget = await storage.create_upload_target(
        user_id=user.id,
        document_id=revision_id,
        name=data.name,
        mime_type=data.mime_type,
        size_bytes=data.size_bytes,
    )

    version = await repo.next_version(user.id, root_id)
    revision = Document(
        id=revision_id,
        user_id=root.user_id,
        application_id=root.application_id,
        type=root.type,
        name=data.name,
        mime_type=data.mime_type,
        size_bytes=data.size_bytes,
        version_label=data.version_label,
        firebase_path=target.storage_path,
        parent_document_id=root.id,
        version=version,
        is_latest_version=True,
    )
    # Demote the previous latest FIRST (a zero-latest window is allowed by
    # the partial unique index; two latests is not).
    group_key = repo._group_key()
    await session.execute(
        sa.update(Document)
        .where(
            Document.user_id == user.id,
            group_key == root.id,
            Document.is_latest_version.is_(True),
            Document.id != revision_id,
        )
        .values(is_latest_version=False)
    )
    session.add(revision)
    await session.flush()
    await session.refresh(revision)
    return document_with_target(revision, target)
```

Add `import sqlalchemy as sa` and `from careeros_api.models.document import Document` to the service imports.

- [ ] **Step 4: Change delete to promote-then-cascade correctly**

Replace `delete_document` with:

```python
async def delete_document(
    session: AsyncSession,
    user: User,
    document_id: uuid.UUID,
    storage: StorageClient,
) -> None:
    """Delete a document (and its storage object).

    Deleting the latest revision promotes the previous revision: the DELETE
    runs first (promoting while the row still exists would violate the
    one-latest-per-group unique index), then the predecessor is promoted.
    Deleting a root cascades to its revisions via the FK.
    """
    repo = DocumentRepository(session)
    document = await repo.get(user.id, document_id)
    if document is None:
        raise NotFoundError(f"Document {document_id} not found")

    root_id = document.parent_document_id or document.id
    was_latest = document.is_latest_version
    firebase_paths = [document.firebase_path]
    if document.parent_document_id is None:
        # Root deletion cascades — collect the revisions' storage paths so
        # the objects don't outlive their metadata.
        for revision in await repo.list_revisions(user.id, document.id):
            firebase_paths.append(revision.firebase_path)

    await repo.delete(document)

    if was_latest and document.parent_document_id is not None:
        group_key = repo._group_key()
        predecessor = (
            await session.execute(
                sa.select(Document)
                .where(Document.user_id == user.id, group_key == root_id)
                .order_by(Document.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if predecessor is not None:
            predecessor.is_latest_version = True
            await session.flush()

    for path in firebase_paths:
        await storage.delete_object(path)
```

- [ ] **Step 5: Add `list_document_revisions`**

```python
async def list_document_revisions(
    session: AsyncSession, user: User, root_id: uuid.UUID
) -> list[DocumentRead]:
    """Revision history of a group (root + revisions, oldest first)."""
    repo = DocumentRepository(session)
    root = await repo.get(user.id, root_id)
    if root is None:
        raise NotFoundError(f"Document {root_id} not found")
    if root.parent_document_id is not None:
        raise ConflictError("Revisions are listed from a root document")
    return [DocumentRead.model_validate(d) for d in await repo.list_revisions(user.id, root_id)]
```

- [ ] **Step 6: Typecheck + lint**

Run: `cd backend && uv run mypy src && uv run ruff check . && uv run ruff format .`
Expected: clean.

- [ ] **Step 7: Commit**

```bash
git add backend/src/careeros_api/services/document.py
git commit -m "feat(api): revision lifecycle — create/list revisions, promote-on-delete"
```

---

### Task 5: Routes

**Files:**
- Modify: `backend/src/careeros_api/api/v1/routes/documents.py`

- [ ] **Step 1: Wire the new endpoints**

Update imports to include `DocumentRevisionCreate` and `ConflictError` (only what's used). Replace the `list_documents` route signature param block and add two routes:

In `list_documents` add:

```python
    include_revisions: bool = Query(False),
```

and pass it through:

```python
    return await document_service.list_documents(
        session,
        current_user,
        limit=limit,
        cursor=cursor,
        application_id=application_id,
        type_filter=type_filter,
        include_revisions=include_revisions,
    )
```

Add after the `create_document` route:

```python
@router.post(
    "/{document_id}/revisions",
    response_model=DocumentUploadTarget,
    status_code=status.HTTP_201_CREATED,
)
async def create_document_revision(
    session: SessionDep,
    current_user: CurrentUserDep,
    document_id: uuid.UUID,
    data: DocumentRevisionCreate,
) -> DocumentUploadTarget:
    """Create a revision of a root document and return an upload target."""
    return await document_service.create_document_revision(
        session, current_user, document_id, data, get_storage_client()
    )


@router.get("/{document_id}/revisions", response_model=list[DocumentRead])
async def list_document_revisions(
    session: SessionDep,
    current_user: CurrentUserDep,
    document_id: uuid.UUID,
) -> list[DocumentRead]:
    """List a document group's revision history (oldest first)."""
    return await document_service.list_document_revisions(session, current_user, document_id)
```

- [ ] **Step 2: Verify ConflictError → 409 mapping**

Run: `cd backend && grep -n "ConflictError\|409" src/careeros_api/errors.py | head`
If ConflictError exists and maps to 409, done. If a differently-named conflict error exists, use it consistently in Tasks 4-5. If none exists, add to `errors.py` following the exact pattern of `NotFoundError` with `status_code = 409`.

- [ ] **Step 3: Import smoke test**

Run: `cd backend && uv run python -c "from careeros_api.main import app; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/src/careeros_api/api/v1/routes/documents.py backend/src/careeros_api/errors.py
git commit -m "feat(api): document revision endpoints + grouped list flag"
```

---

### Task 6: Backend tests

**Files:**
- Modify: `backend/tests/test_documents.py`

- [ ] **Step 1: Add the tests**

Append to `backend/tests/test_documents.py` (helper + 9 tests). These follow the file's existing style:

```python
async def _create_root(
    client: AsyncClient, headers: dict[str, str], doc_type: str = "resume", name: str = "cv.pdf"
) -> str:
    created = await client.post(
        "/api/v1/documents",
        headers=headers,
        json={"type": doc_type, "name": name, "mime_type": "application/pdf"},
    )
    assert created.status_code == 201, created.text
    return created.json()["id"]


async def _add_revision(
    client: AsyncClient, headers: dict[str, str], root_id: str, name: str = "cv v2.pdf"
):
    return await client.post(
        f"/api/v1/documents/{root_id}/revisions",
        headers=headers,
        json={
            "name": name,
            "mime_type": "application/pdf",
            "version_label": "v2 — Python backend",
        },
    )


async def test_revision_created_on_root(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    root_id = await _create_root(client, headers)

    revision = await _add_revision(client, headers, root_id)
    assert revision.status_code == 201, revision.text
    body = revision.json()
    assert body["parent_document_id"] == root_id
    assert body["version"] == 2
    assert body["is_latest_version"] is True
    assert body["version_label"] == "v2 — Python backend"
    assert body["upload_url"]  # same two-step upload flow as roots

    root = (await client.get(f"/api/v1/documents/{root_id}", headers=headers)).json()
    assert root["is_latest_version"] is False


async def test_revision_on_other_users_root_is_404(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    owner, intruder = auth(), auth()
    root_id = await _create_root(client, owner)

    response = await client.post(
        f"/api/v1/documents/{root_id}/revisions",
        headers=intruder,
        json={"name": "steal.pdf"},
    )
    assert response.status_code == 404


async def test_revision_on_non_root_is_409(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    root_id = await _create_root(client, headers)
    revision_id = (await _add_revision(client, headers, root_id)).json()["id"]

    response = await client.post(
        f"/api/v1/documents/{revision_id}/revisions",
        headers=headers,
        json={"name": "depth-3.pdf"},
    )
    assert response.status_code == 409


async def test_grouped_list_returns_one_row_per_group(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    root_a = await _create_root(client, headers, name="a.pdf")
    root_b = await _create_root(client, headers, doc_type="cover_letter", name="b.pdf")
    await _add_revision(client, headers, root_a)

    listed = await client.get("/api/v1/documents", headers=headers)
    assert listed.status_code == 200, listed.text
    page = listed.json()
    by_id = {item["id"]: item for item in page["items"]}
    # root_a's representative is its revision (newest row), not the root.
    assert len(page["items"]) == 2
    assert by_id.keys() != {root_a, root_b} or by_id[root_a]["is_latest_version"] is False
    reps = {item["parent_document_id"] or item["id"] for item in page["items"]}
    assert reps == {root_a, root_b}
    counts = {item["parent_document_id"] or item["id"]: item["revisions_count"] for item in page["items"]}
    assert counts[root_a] == 2
    assert counts[root_b] == 1

    flat = (
        await client.get("/api/v1/documents?include_revisions=true", headers=headers)
    ).json()
    assert len(flat["items"]) == 3
    assert all(item["revisions_count"] is None for item in flat["items"])


async def test_type_filter_with_new_types(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    await _create_root(client, headers, doc_type="visa", name="passport-scan.pdf")
    await _create_root(client, headers, name="cv.pdf")

    listed = await client.get("/api/v1/documents?type=visa", headers=headers)
    assert listed.status_code == 200, listed.text
    assert [item["name"] for item in listed.json()["items"]] == ["passport-scan.pdf"]


async def test_invalid_type_is_422(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    response = await client.post(
        "/api/v1/documents",
        headers=auth(),
        json={"type": "tattoo", "name": "x.pdf"},
    )
    assert response.status_code == 422


async def test_delete_latest_revision_promotes_previous(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    root_id = await _create_root(client, headers)
    revision_id = (await _add_revision(client, headers, root_id)).json()["id"]

    deleted = await client.delete(f"/api/v1/documents/{revision_id}", headers=headers)
    assert deleted.status_code == 204

    root = (await client.get(f"/api/v1/documents/{root_id}", headers=headers)).json()
    assert root["is_latest_version"] is True


async def test_delete_root_cascades(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    root_id = await _create_root(client, headers)
    revision_id = (await _add_revision(client, headers, root_id)).json()["id"]

    deleted = await client.delete(f"/api/v1/documents/{root_id}", headers=headers)
    assert deleted.status_code == 204
    assert (
        await client.get(f"/api/v1/documents/{revision_id}", headers=headers)
    ).status_code == 404


async def test_revision_history_listing(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    headers = auth()
    root_id = await _create_root(client, headers)
    await _add_revision(client, headers, root_id)

    history = await client.get(f"/api/v1/documents/{root_id}/revisions", headers=headers)
    assert history.status_code == 200, history.text
    items = history.json()
    assert [item["version"] for item in items] == [1, 2]

    non_root = items[1]["id"]
    bad = await client.get(f"/api/v1/documents/{non_root}/revisions", headers=headers)
    assert bad.status_code == 409


async def test_version_index_rejects_duplicate(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    """Deterministic race protection: same (group, version) is impossible."""
    import sqlalchemy as sa

    from careeros_api.db.session import get_session_context  # adjust to project's session factory
    from careeros_api.models.document import Document

    headers = auth()
    root_id = await _create_root(client, headers)

    # Direct row insert colliding with the root's version 1.
    from tests.conftest import _engine  # adjust: use the test session fixture instead

    # NOTE: implement inside a session fixture (see conftest's client fixture
    # for how sessions are obtained); insert Document(user_id=<owner>,
    # parent_document_id=root_id, version=1, ...) and expect IntegrityError.
```

**IMPORTANT for the implementer:** the last test (`test_version_index_rejects_duplicate`) must be completed against the project's actual session/fixture pattern — open `tests/conftest.py`, find how the async session/engine fixtures are constructed, and use the same mechanism to insert a colliding row:

```python
async def test_version_index_rejects_duplicate(
    client: AsyncClient, auth: AuthHeaders, require_db: None
) -> None:
    import pytest
    import sqlalchemy as sa
    from sqlalchemy.exc import IntegrityError

    from careeros_api.models.document import Document

    headers = auth()
    root_id = await _create_root(client, headers)
    owner_id = (
        await client.get("/api/v1/me", headers=headers)
    ).json()["id"]  # adjust if /me differs; any endpoint exposing the user id

    # Use the same engine the app fixtures use (see tests/conftest.py).
    from careeros_api.db.session import engine

    async with engine.begin() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(
                sa.insert(Document).values(
                    user_id=owner_id,
                    application_id=None,
                    type="resume",
                    name="collision.pdf",
                    firebase_path="local/dev/collision.pdf",
                    parent_document_id=root_id,
                    version=1,
                    is_latest_version=False,
                )
            )
```

If `/api/v1/me` does not return the user id, capture it via the `auth()` helper's token claims or create the row through a second revision then flipping `version` with a raw UPDATE — any deterministic route to a `(group, version)` collision is acceptable; assert `IntegrityError`.

- [ ] **Step 2: Run the tests**

Run: `cd backend && DATABASE_URL=postgresql+asyncpg://careeros:careeros@localhost:5433/careeros uv run --extra dev pytest tests/test_documents.py -v`
Expected: all PASS (or SKIPPED if DB unreachable — then verify inside `docker compose up -d db` first). Every failure is a real bug to fix before moving on.

- [ ] **Step 3: Full backend gates**

Run: `cd backend && uv run --extra dev pytest && uv run ruff check . && uv run mypy src`
Expected: all green (fake_data.py's pre-existing mypy errors aside).

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_documents.py
git commit -m "test(api): document versioning — isolation, invariants, promotion, cascade"
```

---

### Task 7: Frontend types + api-client

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/services/api-client.ts`

- [ ] **Step 1: Widen the types**

In `frontend/src/types/index.ts`, find the `DocumentType` definition and replace with:

```ts
export type DocumentType =
  | "resume"
  | "cover_letter"
  | "certificate"
  | "reference"
  | "visa"
  | "other"
```

Find the `Document` interface and add (keep existing fields):

```ts
  parent_document_id?: string | null
  version_label?: string | null
  is_latest_version?: boolean
  revisions_count?: number | null
```

- [ ] **Step 2: Extend api-client**

In `frontend/src/services/api-client.ts`, replace the existing `listDocuments` with:

```ts
/** Fetch the caller's documents (grouped: one row per logical document). */
export async function listDocuments(params?: {
  applicationId?: string
  type?: DocumentType
  cursor?: string
  includeRevisions?: boolean
}): Promise<PageOut<Document>> {
  const qs = new URLSearchParams()
  if (params?.applicationId) qs.set("application_id", params.applicationId)
  if (params?.type) qs.set("type", params.type)
  if (params?.cursor) qs.set("cursor", params.cursor)
  if (params?.includeRevisions) qs.set("include_revisions", "true")
  const suffix = qs.size > 0 ? `?${qs.toString()}` : ""
  return apiFetch<PageOut<Document>>(`/documents${suffix}`)
}
```

(If the current signature returns `Document[]` via `unwrapList`, keep call sites compiling: also export a convenience wrapper `listDocumentsFlat` that returns `unwrapList` results for `includeRevisions=true` callers, and update existing call sites to whichever matches their current usage.)

Add:

```ts
/** Fetch a document group's revision history (oldest first). */
export async function listDocumentRevisions(rootId: string): Promise<Document[]> {
  return apiFetch<Document[]>(`/documents/${rootId}/revisions`)
}
```

Ensure `DocumentType` is imported in the type import block.

- [ ] **Step 3: Verify**

Run: `cd frontend && pnpm typecheck`
Expected: clean (fix any call sites that break).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/services/api-client.ts
git commit -m "feat(frontend): document versioning types + api-client"
```

---

### Task 8: Grouping helper + tests

**Files:**
- Create: `frontend/src/features/documents/document-groups.ts`
- Create: `frontend/src/features/documents/document-groups.test.ts`

- [ ] **Step 1: Check the test runner**

Run: `cd frontend && grep -n '"test"' package.json || ls vitest.config.* 2>/dev/null`
If no test runner exists, skip creating the test file and note it in the commit message — do not add a test framework for this (YAGNI); verification is typecheck + usage in Tasks 9-10.

- [ ] **Step 2: Write the helper**

Create `frontend/src/features/documents/document-groups.ts`:

```ts
import type { Document } from "@/types"

/** One logical document: its root, all rows, and the newest representative. */
export type DocumentGroup = {
  rootId: string
  /** Every row of the group, oldest first (root first). */
  revisions: Document[]
  /** The newest row (what the grouped API returns as the list entry). */
  latest: Document
  /** 1 when the group has no revisions yet. */
  count: number
}

/**
 * Merge a flat list of document rows (any mix of roots and revisions, e.g.
 * from `include_revisions=true`) into grouped view models.
 * Rows whose parent is missing from the input are still surfaced under
 * their own rootId so nothing silently disappears.
 */
export function groupDocuments(documents: Document[]): DocumentGroup[] {
  const roots = new Map<string, Document>()
  const byRoot = new Map<string, Document[]>()

  for (const doc of documents) {
    const rootId = doc.parent_document_id ?? doc.id
    if (!doc.parent_document_id) roots.set(doc.id, doc)
    const list = byRoot.get(rootId)
    if (list) {
      list.push(doc)
    } else {
      byRoot.set(rootId, [doc])
    }
  }

  const groups: DocumentGroup[] = []
  for (const [rootId, revisions] of byRoot) {
    const sorted = [...revisions].sort(
      (a, b) =>
        (a.version ?? 1) - (b.version ?? 1) ||
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    )
    groups.push({
      rootId,
      revisions: sorted,
      latest: sorted[sorted.length - 1],
      count: sorted.length,
    })
  }

  // Newest groups first, by their representative row.
  return groups.sort(
    (a, b) =>
      new Date(b.latest.created_at).getTime() - new Date(a.latest.created_at).getTime(),
  )
}

/** Human labels for the 6 document types (single source for chips + badges). */
export const DOCUMENT_TYPE_OPTIONS: { value: DocumentType; label: string }[] = [
  { value: "resume", label: "Resume" },
  { value: "cover_letter", label: "Cover letter" },
  { value: "certificate", label: "Certificate" },
  { value: "reference", label: "Reference" },
  { value: "visa", label: "Visa" },
  { value: "other", label: "Other" },
]

export function documentTypeLabel(type: DocumentType): string {
  return DOCUMENT_TYPE_OPTIONS.find((o) => o.value === type)?.label ?? "Other"
}
```

Add `import type { Document, DocumentType } from "@/types"` at the top.

- [ ] **Step 3: Write tests (only if a runner exists per Step 1)**

Create `frontend/src/features/documents/document-groups.test.ts` covering: single root → one group count 1; root + 2 revisions ordered by version; orphan revision (parent missing) still surfaces; newest-group-first ordering; latest = highest version.

- [ ] **Step 4: Verify + commit**

Run: `cd frontend && pnpm typecheck && pnpm lint`

```bash
git add frontend/src/features/documents/document-groups.ts frontend/src/features/documents/document-groups.test.ts
git commit -m "feat(frontend): document grouping helper + shared type labels"
```

---

### Task 9: Document Manager page + sidebar

**Files:**
- Create: `frontend/src/app/(app)/documents/page.tsx`
- Create: `frontend/src/app/(app)/documents/loading.tsx`
- Create: `frontend/src/features/documents/document-manager.tsx`
- Modify: `frontend/src/components/layout/sidebar.tsx`

- [ ] **Step 1: Server page**

Create `frontend/src/app/(app)/documents/page.tsx`:

```tsx
import type { Metadata } from "next"

import { listDocuments } from "@/services/api-client"
import type { Document, DocumentType } from "@/types"
import { ErrorState } from "@/components/error-state"
import { DocumentManager } from "@/features/documents/document-manager"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Documents",
  description: "Document Manager — resumes, cover letters, and supporting files.",
}

type PageProps = {
  searchParams: Promise<{ type?: string }>
}

export default async function DocumentsPage({ searchParams }: PageProps) {
  const { type } = await searchParams
  const activeType = isDocumentType(type) ? type : undefined

  try {
    const page = await listDocuments(activeType ? { type: activeType } : undefined)
    return <DocumentManager initial={page.items} nextCursor={page.next_cursor} initialType={activeType} />
  } catch (error) {
    return (
      <ErrorState
        title="Couldn't load documents"
        description={error instanceof Error ? error.message : "Please try again."}
      />
    )
  }
}

function isDocumentType(value: string | undefined): value is DocumentType {
  return !!value && ["resume", "cover_letter", "certificate", "reference", "visa", "other"].includes(value)
}
```

- [ ] **Step 2: Loading skeleton**

Create `frontend/src/app/(app)/documents/loading.tsx`:

```tsx
import { Skeleton } from "@/components/ui/skeleton"

export default function Loading() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-9 w-full max-w-md" />
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-full" />
        ))}
      </div>
    </div>
  )
}
```

(Check `@/components/ui/skeleton` exists; if not, use a simple `animate-pulse` div.)

- [ ] **Step 3: Client DocumentManager**

Create `frontend/src/features/documents/document-manager.tsx`. Structure (client component):

```tsx
"use client"
```

Props: `{ initial: Document[]; nextCursor: string | null; initialType?: DocumentType }`.

Behaviour:
- Filter chips from `DOCUMENT_TYPE_OPTIONS` + an "All" chip. Active chip = `aria-pressed`. Clicking navigates via `router.push(type ? `/documents?type=${type}` : "/documents")` (server re-renders with the new first page).
- Group cards rendered from `initial` — each `Document` from the grouped API **is** the group's representative; display `name`, type badge (`documentTypeLabel`), `version_label`, `v{version}`, `revisions_count`, `updated_at`, and buttons: **Add version** and expand toggle.
- Expansion: on first expand, fetch `listDocumentRevisions(rootIdFor(doc))` where `rootIdFor = doc.parent_document_id ?? doc.id`; cache in component state; render the revision rows (version, label, updated_at).
- **Add version**: file input → `createDocumentRevision` server action (Task 10) → upload bytes to the returned `upload_url` (same pattern as `documents-panel.tsx`'s upload) → `router.refresh()`.
- **Load more**: button shown when `nextCursor` (or a subsequently fetched cursor) is non-null; fetches `listDocuments({ type, cursor })`, appends.
- Empty state when no groups: "No documents yet — upload your first resume."
- Upload button for new roots (reuse the upload dialog pattern from the panel: type selector from `DOCUMENT_TYPE_OPTIONS`, optional `version_label` input).

Rendering must stay accessible: chips as `<button aria-pressed>`, groups in a `<ul>`, expand states wired to `aria-expanded`.

- [ ] **Step 4: Sidebar entry**

In `frontend/src/components/layout/sidebar.tsx`, add to the "Main" items after Applications:

```tsx
{ label: "Documents", href: "/documents", icon: FileText },
```

and add `FileText` to the lucide import list.

- [ ] **Step 5: Verify**

Run: `cd frontend && pnpm typecheck && pnpm lint`
Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add "frontend/src/app/(app)/documents" frontend/src/features/documents/document-manager.tsx frontend/src/components/layout/sidebar.tsx
git commit -m "feat(frontend): document manager page with type filters and version groups"
```

---

### Task 10: Workspace panel + server actions

**Files:**
- Modify: `frontend/src/features/documents/actions.ts`
- Modify: `frontend/src/features/documents/documents-panel.tsx`

- [ ] **Step 1: Add revision actions**

In `frontend/src/features/documents/actions.ts` add:

```ts
/** Input for creating a revision (matches POST /documents/{id}/revisions). */
export type CreateRevisionInput = {
  rootId: string
  name: string
  mime_type: string
  size_bytes: number
  version_label?: string
}

export type CreateRevisionResult = {
  ok: boolean
  document?: Document
  error?: string
}

export async function createDocumentRevision(
  input: CreateRevisionInput,
): Promise<CreateRevisionResult> {
  try {
    const document = await apiFetch<Document>(`/documents/${input.rootId}/revisions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: input.name,
        mime_type: input.mime_type,
        size_bytes: input.size_bytes,
        version_label: input.version_label || undefined,
      }),
    })
    revalidatePath("/documents")
    return { ok: true, document }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}
```

`deleteDocument` gains a `revalidatePath("/documents")` line next to the application one.

- [ ] **Step 2: Update the panel**

In `frontend/src/features/documents/documents-panel.tsx`:

1. Delete the local `DOCUMENT_TYPE_OPTIONS` (it wrongly contains `offer_letter` — a value that isn't even in the backend enum) and import the shared one from `./document-groups`.
2. Fetch with `include_revisions: true` (flat list scoped by `application_id`) and group client-side with `groupDocuments`.
3. Render each group: representative name + `v{version}` + `revisions_count` badge; expandable revision list (fetched lazily or built from the already-flat data — prefer the latter: the flat fetch already contains every revision).
4. **Add version** button per group: file picker → `createDocumentRevision` → upload bytes to `upload_url` (reuse the existing upload snippet) → optimistic refresh via `router.refresh()` or re-fetch.
5. Delete action unchanged but available per revision row.

- [ ] **Step 3: Verify + commit**

Run: `cd frontend && pnpm typecheck && pnpm lint && pnpm build`

```bash
git add frontend/src/features/documents/actions.ts frontend/src/features/documents/documents-panel.tsx
git commit -m "feat(frontend): grouped workspace documents panel with add-version"
```

---

### Task 11: API docs + full verification

**Files:**
- Modify: `docs/API.md`

- [ ] **Step 1: Document the API**

In `docs/API.md`, extend the Documents section with:

```markdown
### Documents

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/documents` | Grouped by default: one row per logical document (the newest row of each group) with `revisions_count`. `?include_revisions=true` returns every row flat. Filters: `application_id`, `type` (`resume\|cover_letter\|certificate\|reference\|visa\|other`). Keyset pagination. |
| POST | `/api/v1/documents` | Create a root document; optional `version_label`. Returns upload target. |
| GET | `/api/v1/documents/{id}` | Single document (root or revision). |
| DELETE | `/api/v1/documents/{id}` | Delete a row. Root deletion cascades to revisions. Deleting the latest revision promotes the previous one. |
| POST | `/api/v1/documents/{id}/revisions` | Create a revision of a caller-owned **root** (`409` if `{id}` is itself a revision). `type`/`application_id` are inherited. Returns upload target. |
| GET | `/api/v1/documents/{id}/revisions` | Group history oldest-first; `{id}` must be a caller-owned root (`409` otherwise). |
```

(Adapt formatting to the file's existing conventions.)

- [ ] **Step 2: Full verification sweep**

```bash
cd backend && uv run --extra dev pytest && uv run ruff check . && uv run ruff format --check . && uv run mypy src
cd ../frontend && pnpm lint && pnpm typecheck && pnpm build
cd .. && grep -n "ix_documents" backend/src/careeros_api/models/document.py backend/alembic/versions/0011_document_versioning.py
```

Expected: all green; the index names appear identically in both files (no ORM/migration drift).

- [ ] **Step 3: Final commits**

```bash
git add docs/API.md
git commit -m "docs(api): document versioning endpoints"
```

---

## Self-Review (completed during planning)

- **Spec coverage:** §2.1-2.3 → Task 1; §2.4-2.5 → Tasks 3-4; §2.6 → Task 1; §3.1-3.4 → Tasks 2, 4, 5; §4.1-4.5 → Tasks 7-10; §5.1 → Task 6; §5.2 → Task 8; §6 checklist → Task 11.
- **Placeholders:** the only intentional "adjust" notes are where the plan cannot see fixture internals (`test_version_index_rejects_duplicate` session access, `skeleton` component existence, `ConflictError` name) — each includes concrete fallback instructions, not vague TODOs.
- **Type consistency:** `DocumentRevisionCreate` (Task 2) ↔ service (Task 4) ↔ route (Task 5); `DocumentGroup`/`groupDocuments`/`DOCUMENT_TYPE_OPTIONS` (Task 8) reused verbatim in Tasks 9-10; `CreateRevisionInput` (Task 10) matches the API body from Task 5.
