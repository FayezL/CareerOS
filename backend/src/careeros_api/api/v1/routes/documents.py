"""Endpoints for the authenticated user's documents (``/api/v1/documents``)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Response, UploadFile, status

from careeros_api.api.deps import CurrentUserDep, SessionDep
from careeros_api.core.storage import get_storage_client
from careeros_api.schemas.common import PageOut
from careeros_api.schemas.document import (
    DocumentCreate,
    DocumentRead,
    DocumentRevisionCreate,
    DocumentType,
    DocumentUploadTarget,
)
from careeros_api.services import document as document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=PageOut[DocumentRead])
async def list_documents(
    session: SessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    application_id: uuid.UUID | None = Query(None),
    type_filter: DocumentType | None = Query(None, alias="type"),
    include_revisions: bool = Query(False),
) -> PageOut[DocumentRead]:
    """Page through the caller's documents with optional filters."""
    return await document_service.list_documents(
        session,
        current_user,
        limit=limit,
        cursor=cursor,
        application_id=application_id,
        type_filter=type_filter,
        include_revisions=include_revisions,
    )


@router.post(
    "",
    response_model=DocumentUploadTarget,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    session: SessionDep,
    current_user: CurrentUserDep,
    data: DocumentCreate,
) -> DocumentUploadTarget:
    """Create document metadata and return an upload target."""
    return await document_service.create_document(session, current_user, data, get_storage_client())


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


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    session: SessionDep,
    current_user: CurrentUserDep,
    document_id: uuid.UUID,
) -> DocumentRead:
    """Return a single document owned by the caller."""
    return await document_service.get_document(session, current_user, document_id)


@router.post("/{document_id}/upload", response_model=DocumentRead)
async def upload_document_file(
    session: SessionDep,
    current_user: CurrentUserDep,
    document_id: uuid.UUID,
    file: UploadFile,
) -> DocumentRead:
    """Receive the file bytes for a document (local storage flow)."""
    data = await file.read()
    return await document_service.upload_document_bytes(
        session, current_user, document_id, data, get_storage_client()
    )


@router.delete("/{document_id}")
async def delete_document(
    session: SessionDep,
    current_user: CurrentUserDep,
    document_id: uuid.UUID,
) -> Response:
    """Delete a document and its underlying storage object."""
    await document_service.delete_document(session, current_user, document_id, get_storage_client())
    return Response(status_code=status.HTTP_204_NO_CONTENT)
