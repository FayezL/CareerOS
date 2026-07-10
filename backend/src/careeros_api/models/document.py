"""Document ORM model."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from careeros_api.db.base import Base
from careeros_api.db.mixins import TimestampMixin, UUIDPrimaryKey

document_type = sa.Enum(
    "resume",
    "cover_letter",
    "other",
    name="document_type",
    native_enum=True,
)


class Document(UUIDPrimaryKey, TimestampMixin, Base):
    """Metadata for a file stored in object storage.

    Only metadata lives in Postgres; the file bytes live in object storage and
    are addressed by ``firebase_path``.
    """

    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_user_id_type", "user_id", "type"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    type: Mapped[str] = mapped_column(document_type, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    firebase_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
