"""ApplicationStageHistory ORM model (append-only audit table)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from careeros_api.db.base import Base
from careeros_api.db.mixins import UUIDPrimaryKey
from careeros_api.models.pipeline_stage import PipelineStage


class ApplicationStageHistory(UUIDPrimaryKey, Base):
    """An immutable record of a single stage transition for an application."""

    __tablename__ = "application_stage_history"
    __table_args__ = (
        Index(
            "ix_application_stage_history_application_id_changed_at",
            "application_id",
            "changed_at",
        ),
    )

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    from_stage_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pipeline_stages.id", ondelete="RESTRICT"),
        nullable=True,
    )
    to_stage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pipeline_stages.id", ondelete="RESTRICT"),
        nullable=False,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    from_stage: Mapped[PipelineStage | None] = relationship(
        PipelineStage, foreign_keys=[from_stage_id]
    )
    to_stage: Mapped[PipelineStage] = relationship(PipelineStage, foreign_keys=[to_stage_id])
