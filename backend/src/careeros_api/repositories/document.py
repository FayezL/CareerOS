"""Repository for the ``Document`` model (all reads scoped by ``user_id``)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import ColumnExpressionArgument, select
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.models.document import Document
from careeros_api.repositories.base import BaseRepository
from careeros_api.schemas.document import DocumentCreate


class DocumentRepository(BaseRepository[Document]):
    """Data access for documents belonging to a single user."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Document)

    async def list(  # type: ignore[override]
        self,
        user_id: uuid.UUID,
        *,
        limit: int,
        cursor: str | None = None,
        application_id: uuid.UUID | None = None,
        type_filter: str | None = None,
    ) -> tuple[Sequence[Document], str | None]:
        """Page through a user's documents with optional filters."""

        def build_filters() -> list[ColumnExpressionArgument[bool]]:
            conditions: list[ColumnExpressionArgument[bool]] = []
            if application_id is not None:
                conditions.append(Document.application_id == application_id)
            if type_filter is not None:
                conditions.append(Document.type == type_filter)
            return conditions

        return await self.list_paginated(
            user_id,
            limit=limit,
            cursor=cursor,
            filters_builder=build_filters,
        )

    async def get(self, user_id: uuid.UUID, document_id: uuid.UUID) -> Document | None:
        """Return the document if it exists and belongs to ``user_id``."""
        stmt = select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: uuid.UUID,
        data: DocumentCreate,
        firebase_path: str,
        document_id: uuid.UUID | None = None,
    ) -> Document:
        """Insert a new document owned by ``user_id`` (optional explicit id)."""
        kwargs: dict[str, object] = {}
        if document_id is not None:
            kwargs["id"] = document_id
        document = Document(
            user_id=user_id,
            application_id=data.application_id,
            type=data.type,
            name=data.name,
            mime_type=data.mime_type,
            size_bytes=data.size_bytes,
            firebase_path=firebase_path,
            **kwargs,
        )
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)
        return document

    async def delete(self, document: Document) -> None:
        """Hard-delete ``document`` (documents have no soft-delete)."""
        await self.session.delete(document)
        await self.session.flush()
