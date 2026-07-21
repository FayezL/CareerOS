"""Tag business-logic services.

Tags are managed inline from the application form (no standalone CRUD page):
the user types or picks tags, and ``resolve_names`` creates-or-reuses them
case-insensitively. A curated default set is seeded on first access so the
picker isn't empty.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.errors import ConflictError, NotFoundError
from careeros_api.models.user import User
from careeros_api.repositories.tag import TagRepository
from careeros_api.schemas.tag import TagCreate, TagRead

# Curated starter library, seeded for first-time users. Users can rename,
# recolour, or delete any of these; they are not special at the data layer.
_DEFAULT_TAGS: list[str] = [
    "Remote",
    "Hybrid",
    "Onsite",
    "Visa Sponsorship",
    "Senior",
    "Mid-level",
    "Junior",
    "Backend",
    "Frontend",
    "Fullstack",
    "Python",
    "Go",
    "TypeScript",
    "React",
    "Startup",
    "Europe",
    "Germany",
    "Netherlands",
    "USA",
    "UK",
]


async def ensure_default_tags(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Seed the curated default tag set for ``user_id`` if they have none."""
    repo = TagRepository(session)
    if await repo.count(user_id) > 0:
        return
    for name in _DEFAULT_TAGS:
        await repo.create(user_id, name=name)
    await session.flush()


async def list_tags(session: AsyncSession, user: User) -> list[TagRead]:
    """Return the caller's tags, seeding defaults on first access."""
    repo = TagRepository(session)
    if await repo.count(user.id) == 0:
        await ensure_default_tags(session, user.id)
        await session.commit()
    rows = await repo.list_all(user.id)
    return [TagRead.model_validate(t) for t in rows]


async def create_tag(session: AsyncSession, user: User, data: TagCreate) -> TagRead:
    """Create a tag explicitly. Rejects a case-insensitive duplicate name."""
    repo = TagRepository(session)
    if await repo.get_by_name(user.id, data.name) is not None:
        raise ConflictError(f"A tag named {data.name!r} already exists")
    tag = await repo.create(user.id, name=data.name, color=data.color)
    return TagRead.model_validate(tag)


async def delete_tag(session: AsyncSession, user: User, tag_id: uuid.UUID) -> None:
    repo = TagRepository(session)
    tag = await repo.get(user.id, tag_id)
    if tag is None:
        raise NotFoundError(f"Tag {tag_id} not found")
    await repo.delete(tag)
