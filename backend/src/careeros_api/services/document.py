"""Document business-logic services."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.core.storage import StorageClient, UploadTarget
from careeros_api.errors import NotFoundError
from careeros_api.models.user import User
from careeros_api.repositories.application import ApplicationRepository
from careeros_api.repositories.document import DocumentRepository
from careeros_api.schemas.common import PageOut
from careeros_api.schemas.document import (
    DocumentCreate,
    DocumentRead,
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
) -> PageOut[DocumentRead]:
    """Return one page of the caller's documents."""
    repo = DocumentRepository(session)
    items, next_cursor = await repo.list(
        user.id,
        limit=limit,
        cursor=cursor,
        application_id=application_id,
        type_filter=type_filter,
    )
    return PageOut(items=[DocumentRead.model_validate(d) for d in items], next_cursor=next_cursor)


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
    """Delete document metadata and its underlying storage object."""
    repo = DocumentRepository(session)
    document = await repo.get(user.id, document_id)
    if document is None:
        raise NotFoundError(f"Document {document_id} not found")
    storage_path = document.firebase_path
    await repo.delete(document)
    await storage.delete_object(storage_path)
