"""Document ORM model."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from careeros_api.db.base import Base
from careeros_api.db.mixins import TimestampMixin, UUIDPrimaryKey

document_type = sa.Enum(
    "resume",
    "cover_letter",
    "certificate",
    "reference",
    "visa",
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
    __table_args__ = (
        Index(
            "ix_documents_user_type_created_at",
            "user_id",
            "type",
            text("created_at DESC"),
            text("id DESC"),
        ),
        Index("ix_documents_parent_document_id", "parent_document_id"),
        Index(
            "ix_documents_one_latest_per_group",
            text("COALESCE(parent_document_id, id)"),
            unique=True,
            postgresql_where=text("is_latest_version = true"),
        ),
        Index(
            "ix_documents_group_version",
            text("COALESCE(parent_document_id, id)"),
            text("version"),
            unique=True,
        ),
    )

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
    parent_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
    )
    type: Mapped[str] = mapped_column(document_type, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    firebase_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    version_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_latest_version: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=True,
        server_default=sa.text("true"),
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
