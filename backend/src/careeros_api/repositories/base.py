"""Generic, session-scoped repositories with cursor pagination."""

from __future__ import annotations

import base64
import uuid
from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Any, cast

from sqlalchemy import ColumnExpressionArgument, select
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapper

from careeros_api.db.base import Base
from careeros_api.models.user import User

FilterBuilder = Callable[[], Sequence[ColumnExpressionArgument[bool]]]


def encode_cursor(created_at: datetime, entity_id: uuid.UUID) -> str:
    """Encode ``(created_at, id)`` as a URL-safe, padding-free base64 cursor."""
    payload = f"{created_at.isoformat()}|{entity_id}".encode()
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    """Inverse of :func:`encode_cursor`.

    Raises:
        ValueError: If the cursor cannot be decoded into a timestamp and UUID.
    """
    padding = "=" * (-len(cursor) % 4)
    try:
        raw = base64.urlsafe_b64decode(cursor + padding).decode("utf-8")
        created_at_str, entity_id_str = raw.rsplit("|", 1)
        return datetime.fromisoformat(created_at_str), uuid.UUID(entity_id_str)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Invalid cursor") from exc


class BaseRepository[ModelT: Base]:
    """Minimal data-access helper bound to a session and a model class."""

    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    def _column(self, name: str) -> Any:
        """Resolve a mapped column by name (used for generic filtering)."""
        mapper = cast("Mapper[Any]", sa_inspect(self.model))
        return mapper.columns[name]

    async def get_by_id(self, entity_id: uuid.UUID | int | str) -> ModelT | None:
        return await self.session.get(self.model, entity_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> Sequence[ModelT]:
        result = await self.session.execute(select(self.model).limit(limit).offset(offset))
        return result.scalars().all()

    async def list_paginated(
        self,
        user_id: uuid.UUID,
        *,
        limit: int,
        cursor: str | None = None,
        filters_builder: FilterBuilder | None = None,
        options: Sequence[Any] | None = None,
    ) -> tuple[Sequence[ModelT], str | None]:
        """Keyset-paginated listing scoped to ``user_id``.

        Rows are ordered by ``created_at DESC, id DESC``. A cursor encodes the
        last row's ``(created_at, id)``; the next page selects rows that sort
        strictly before it. ``filters_builder`` may supply additional WHERE
        conditions (e.g. search, status) and ``options`` may supply loader
        options (e.g. eager-loaded relationships). Returns ``(rows,
        next_cursor)`` where ``next_cursor`` is ``None`` when no further rows
        remain.
        """
        created_at_col = self._column("created_at")
        id_col = self._column("id")
        user_id_col = self._column("user_id")

        stmt = select(self.model).where(user_id_col == user_id)
        if options:
            stmt = stmt.options(*options)
        if filters_builder is not None:
            stmt = stmt.where(*filters_builder())

        if cursor is not None:
            cursor_at, cursor_id = decode_cursor(cursor)
            stmt = stmt.where(
                (created_at_col < cursor_at)
                | ((created_at_col == cursor_at) & (id_col < cursor_id))
            )

        stmt = stmt.order_by(created_at_col.desc(), id_col.desc()).limit(limit + 1)
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())

        next_cursor: str | None = None
        if len(rows) > limit:
            last: Any = rows[limit - 1]
            last_at = cast(datetime, last.created_at)
            last_id = cast(uuid.UUID, last.id)
            next_cursor = encode_cursor(last_at, last_id)
            rows = rows[:limit]

        return rows, next_cursor


class UserRepository(BaseRepository[User]):
    """Repository for the ``User`` model."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_clerk_id(self, clerk_user_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.clerk_user_id == clerk_user_id))
        return result.scalar_one_or_none()
