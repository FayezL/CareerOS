"""Timeline event ORM model.

A free-form activity log entry on an application (recruiter viewed, email sent,
phone screen, take-home, note, custom …). Lives **alongside**
``application_stage_history`` (which records stage transitions only); the
workspace timeline merges both, ordered by time.

``event_type`` is a native enum with a ``CUSTOM`` escape hatch — the UI shows a
free-text ``summary`` when the user picks ``CUSTOM``. ``source`` defaults to
``'user'`` and exists so the table can later hold system-generated activity
entries without a migration.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from careeros_api.db.base import Base
from careeros_api.db.mixins import TimestampMixin, UUIDPrimaryKey


class TimelineEventType(enum.Enum):
    APPLIED = "APPLIED"
    EMAIL = "EMAIL"
    CALL = "CALL"
    FOLLOW_UP = "FOLLOW_UP"
    PHONE_SCREEN = "PHONE_SCREEN"
    TECHNICAL = "TECHNICAL"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"
    ONSITE = "ONSITE"
    TAKE_HOME = "TAKE_HOME"
    RECRUITER_MESSAGE = "RECRUITER_MESSAGE"
    OFFER = "OFFER"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    NOTE = "NOTE"
    CUSTOM = "CUSTOM"


class TimelineImportance(enum.Enum):
    NORMAL = "NORMAL"
    IMPORTANT = "IMPORTANT"
    MILESTONE = "MILESTONE"


class TimelineEvent(UUIDPrimaryKey, TimestampMixin, Base):
    """A single dated activity entry on an application's timeline."""

    __tablename__ = "timeline_events"
    __table_args__ = (
        Index(
            "ix_timeline_events_application_id_occurred_at",
            "application_id",
            "occurred_at",
            "id",
        ),
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
    event_type: Mapped[TimelineEventType] = mapped_column(
        sa.Enum(TimelineEventType, name="timeline_event_type"),
        nullable=False,
    )
    summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    importance: Mapped[TimelineImportance] = mapped_column(
        sa.Enum(TimelineImportance, name="timeline_importance"),
        nullable=False,
        default=TimelineImportance.NORMAL,
        server_default="NORMAL",
    )
    follow_up_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="user",
        server_default="user",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<TimelineEvent {self.event_type!r} @ {self.occurred_at}>"


__all__ = ["TimelineEvent", "TimelineEventType", "TimelineImportance"]
