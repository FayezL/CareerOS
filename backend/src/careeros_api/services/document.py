"""Document business-logic services."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.core.storage import StorageClient, UploadTarget
from careeros_api.errors import ConflictError, NotFoundError
from careeros_api.models.document import Document
from careeros_api.models.user import User
from careeros_api.repositories.application import ApplicationRepository
from careeros_api.repositories.document import DocumentRepository
from careeros_api.schemas.common import PageOut
from careeros_api.schemas.document import (
    DocumentCreate,
    DocumentRead,
    DocumentRevisionCreate,
    DocumentUploadTarget,
    document_with_target,
)


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
        flat_items, next_cursor = await repo.list(
            user.id,
            limit=limit,
            cursor=cursor,
            application_id=application_id,
            type_filter=type_filter,
        )
        return PageOut(
            items=[DocumentRead.model_validate(d) for d in flat_items], next_cursor=next_cursor
        )

    rows, next_cursor, counts = await repo.list_groups(
        user.id,
        limit=limit,
        cursor=cursor,
        application_id=application_id,
        type_filter=type_filter,
    )
    items: list[DocumentRead] = []
    for d in rows:
        doc_read = DocumentRead.model_validate(d)
        doc_read.revisions_count = counts.get(repo._root_id_of(d), 1)
        items.append(doc_read)
    return PageOut(items=items, next_cursor=next_cursor)


async def get_document(session: AsyncSession, user: User, document_id: uuid.UUID) -> DocumentRead:
    """Return a single document owned by the caller."""
    repo = DocumentRepository(session)
    document = await repo.get(user.id, document_id)
    if document is None:
        raise NotFoundError(f"Document {document_id} not found")
    return DocumentRead.model_validate(document)


async def create_document(
    session: AsyncSession,
    user: User,
    data: DocumentCreate,
    storage: StorageClient,
) -> DocumentUploadTarget:
    """Create document metadata and return an upload target for its bytes.

    When ``application_id`` is supplied it must belong to the caller; otherwise a
    ``NotFoundError`` is raised so existence is never leaked.
    """
    if data.application_id is not None:
        app_repo = ApplicationRepository(session)
        if await app_repo.get(user.id, data.application_id) is None:
            raise NotFoundError(f"Application {data.application_id} not found")

    # Generate the document id once so the storage target's upload URL and the
    # persisted row share the same identifier (otherwise the URL pointed at a
    # different, randomly-generated id).
    document_id = uuid.uuid4()
    target: UploadTarget = await storage.create_upload_target(
        user_id=user.id,
        document_id=document_id,
        name=data.name,
        mime_type=data.mime_type,
        size_bytes=data.size_bytes,
    )
    repo = DocumentRepository(session)
    document = await repo.create(user.id, data, target.storage_path, document_id=document_id)
    await session.flush()
    return document_with_target(document, target)


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


async def upload_document_bytes(
    session: AsyncSession,
    user: User,
    document_id: uuid.UUID,
    data: bytes,
    storage: StorageClient,
) -> DocumentRead:
    """Persist the uploaded bytes for an existing local document."""
    repo = DocumentRepository(session)
    document = await repo.get(user.id, document_id)
    if document is None:
        raise NotFoundError(f"Document {document_id} not found")
    await storage.save_bytes(storage_path=document.firebase_path, data=data)
    if document.size_bytes is None:
        document.size_bytes = len(data)
    await session.flush()
    await session.refresh(document)
    return DocumentRead.model_validate(document)


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
