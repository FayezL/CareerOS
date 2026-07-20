"""Timeline event ORM model.

A free-form activity log entry on an application (recruiter viewed, email sent,
phone screen, take-home, custom …). Lives **alongside** ``application_stage_*-
``history`` (which records stage transitions only); the workspace timeline
merges both, ordered by time.

``event_type`` is a plain string rather than a native enum so user-defined
custom event types are first-class — the app validates against a curated set
but any string is allowed at the data layer.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from careeros_api.db.base import Base
from careeros_api.db.mixins import TimestampMixin, UUIDPrimaryKey


class TimelineEvent(UUIDPrimaryKey, TimestampMixin, Base):
    """A single dated activity entry on an application's timeline."""

    __tablename__ = "timeline_events"
    __table_args__ = (
        # Hot read: an application's timeline, newest first.
        Index(
            "ix_timeline_events_application_id_occurred_at",
            "application_id",
            "occurred_at",
            "id",
        ),
        # Cross-application activity feed (dashboard "recent activity").
        Index("ix_timeline_events_user_id_occurred_at", "user_id", "occurred_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<TimelineEvent {self.event_type!r} @ {self.occurred_at}>"


__all__ = ["TimelineEvent"]
