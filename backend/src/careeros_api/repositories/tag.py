"""Repository for the ``Tag`` model (all reads scoped by ``user_id``)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.models.tag import Tag
from careeros_api.repositories.base import BaseRepository


class TagRepository(BaseRepository[Tag]):
    """Data access for tags belonging to a single user."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Tag)

    async def count(self, user_id: uuid.UUID) -> int:
        """Number of tags owned by ``user_id``."""
        stmt = select(func.count()).select_from(Tag).where(Tag.user_id == user_id)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def list_all(self, user_id: uuid.UUID) -> list[Tag]:
        """Return all of the caller's tags ordered by name."""
        stmt = select(Tag).where(Tag.user_id == user_id).order_by(Tag.name.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, user_id: uuid.UUID, tag_id: uuid.UUID) -> Tag | None:
        stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, user_id: uuid.UUID, name: str) -> Tag | None:
        """Case-insensitive exact-name lookup for the caller."""
        stmt = select(Tag).where(
            Tag.user_id == user_id,
            func.lower(Tag.name) == func.lower(name),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, *, name: str, color: str | None = None) -> Tag:
        tag = Tag(user_id=user_id, name=name, color=color)
        self.session.add(tag)
        await self.session.flush()
        await self.session.refresh(tag)
        return tag

    async def resolve_names(
        self,
        user_id: uuid.UUID,
        names: list[str],
    ) -> list[Tag]:
        """Resolve a list of tag names to Tag rows, creating any that don't exist.

        Names are matched case-insensitively against existing tags so "python"
        reuses an existing "Python". New tags are created without a colour;
        the caller can edit later. Deduplicates the input (case-insensitive).
        """
        # Preserve order, dedupe case-insensitively, drop empties.
        seen: set[str] = set()
        unique_names: list[str] = []
        for n in names:
            cleaned = n.strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            unique_names.append(cleaned)

        resolved: list[Tag] = []
        for name in unique_names:
            existing = await self.get_by_name(user_id, name)
            if existing is not None:
                resolved.append(existing)
            else:
                resolved.append(await self.create(user_id, name=name))
        return resolved

    async def delete(self, tag: Tag) -> None:
        await self.session.delete(tag)
        await self.session.flush()
