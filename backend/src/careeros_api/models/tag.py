"""Tag ORM model + the Application↔Tag association table.

Tags are user-scoped labels (Remote, Visa Sponsorship, Python, Europe, …) used
for filtering and analytics. They are managed inline from the application form
(no standalone Tags CRUD page) and surfaced as badges on every list/workspace.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, ForeignKey, Index, String, Table, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from careeros_api.db.base import Base
from careeros_api.db.mixins import TimestampMixin, UUIDPrimaryKey

# Association table — many-to-many between applications and tags. Declared at
# module scope so it can be referenced before the Application model is defined.
# `index=True` on tag_id auto-creates `ix_application_tags_tag_id` (matches
# migration 0009) for the reverse lookup "all applications with this tag".
application_tags = Table(
    "application_tags",
    Base.metadata,
    Column(
        "application_id",
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)


class Tag(UUIDPrimaryKey, TimestampMixin, Base):
    """A user-scoped label that can be attached to any number of applications."""

    __tablename__ = "tags"
    __table_args__ = (
        # Unique per (user, case-insensitive name). Declared as a unique Index
        # (not UniqueConstraint) so the text("lower(name)") functional
        # expression is accepted — matches the companies.name pattern.
        Index(
            "uq_tags_user_id_name_lower",
            "user_id",
            text("lower(name)"),
            unique=True,
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[str | None] = mapped_column(String(64), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Tag {self.name!r}>"


__all__ = ["Tag", "application_tags"]
