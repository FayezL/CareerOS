"""PipelineStage ORM model."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from careeros_api.db.base import Base
from careeros_api.db.mixins import TimestampMixin, UUIDPrimaryKey


class PipelineStage(UUIDPrimaryKey, TimestampMixin, Base):
    """A user-configurable funnel stage (Kanban board column).

    Stages are modeled as data rows (not an enum) so a user can rename,
    re-color, and reorder their pipeline freely.
    """

    __tablename__ = "pipeline_stages"
    __table_args__ = (
        UniqueConstraint("user_id", "position", name="uq_pipeline_stages_user_id_position"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str | None] = mapped_column(String, nullable=True)
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
