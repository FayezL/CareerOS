"""Document request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from careeros_api.core.storage import UploadTarget

DocumentType = Literal["resume", "cover_letter", "certificate", "reference", "visa", "other"]


class DocumentCreate(BaseModel):
    """Payload to create document metadata and request an upload target."""

    application_id: uuid.UUID | None = None
    type: DocumentType
    name: str = Field(..., min_length=1, max_length=255)
    mime_type: str | None = Field(default=None, max_length=255)
    size_bytes: int | None = Field(default=None, ge=0)
    version_label: str | None = Field(default=None, max_length=255)


class DocumentRevisionCreate(BaseModel):
    """Payload to create a new revision of an existing root document."""

    name: str = Field(..., min_length=1, max_length=255)
    mime_type: str | None = Field(default=None, max_length=255)
    size_bytes: int | None = Field(default=None, ge=0)
    version_label: str | None = Field(default=None, max_length=255)


class DocumentRead(BaseModel):
    """Public representation of a document."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID | None
    type: DocumentType
    name: str
    firebase_path: str
    mime_type: str | None
    size_bytes: int | None
    version: int
    parent_document_id: uuid.UUID | None = None
    version_label: str | None = None
    is_latest_version: bool = True
    # Populated only on grouped list reads; None on flat/single reads.
    revisions_count: int | None = None
    created_at: datetime
    updated_at: datetime


class DocumentUploadTarget(DocumentRead):
    """A freshly-created document plus its one-time upload instructions."""

    upload_url: str
    upload_method: str
    upload_headers: dict[str, str] = {}
    expires_at: datetime | None = None


def document_with_target(document: object, target: UploadTarget) -> DocumentUploadTarget:
    """Build a ``DocumentUploadTarget`` from an ORM row and an upload target."""
    base = DocumentRead.model_validate(document)
    return DocumentUploadTarget(
        **base.model_dump(),
        upload_url=target.upload_url,
        upload_method=target.upload_method,
        upload_headers=target.upload_headers,
        expires_at=target.expires_at,
    )
