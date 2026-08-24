"""Repository for the ``Document`` model (all reads scoped by ``user_id``)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import ColumnExpressionArgument, select
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.models.document import Document
from careeros_api.repositories.base import BaseRepository, decode_cursor, encode_cursor
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

    @staticmethod
    def _group_key() -> sa.Label[uuid.UUID]:
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

    async def list_revisions(self, user_id: uuid.UUID, root_id: uuid.UUID) -> Sequence[Document]:
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
