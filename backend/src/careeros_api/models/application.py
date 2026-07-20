"""Application ORM model."""

from __future__ import annotations

import uuid
from datetime import date

import sqlalchemy as sa
from sqlalchemy import Date, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from careeros_api.db.base import Base
from careeros_api.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey
from careeros_api.models.company import Company
from careeros_api.models.pipeline_stage import PipelineStage
from careeros_api.models.tag import Tag, application_tags

application_status = sa.Enum(
    "active",
    "archived",
    "rejected",
    "accepted",
    name="application_status",
    native_enum=True,
)

rejection_reason_category = sa.Enum(
    "visa_sponsorship",
    "lack_of_experience",
    "salary",
    "culture_fit",
    "position_filled",
    "no_feedback",
    "other",
    name="rejection_reason_category",
    native_enum=True,
)


class Application(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """A single job application tracked by a user against a company."""

    __tablename__ = "applications"
    __table_args__ = (
        Index(
            "ix_applications_user_id_created_at_id",
            "user_id",
            text("created_at DESC"),
            text("id DESC"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    role_title: Mapped[str] = mapped_column(String, nullable=False)
    current_stage_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pipeline_stages.id", ondelete="RESTRICT"),
        index=True,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        application_status,
        nullable=False,
        default="active",
        server_default="active",
    )
    job_url: Mapped[str | None] = mapped_column(String, nullable=True)
    job_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    applied_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Captured when an application is rejected; surfaced in the timeline and
    # aggregated in analytics (most common rejection reasons).
    rejection_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rejection_reason_category: Mapped[str | None] = mapped_column(
        rejection_reason_category, nullable=True
    )

    company: Mapped[Company] = relationship(
        Company,
        foreign_keys=[company_id],
        backref="applications",
    )
    current_stage: Mapped[PipelineStage | None] = relationship(
        PipelineStage,
        foreign_keys=[current_stage_id],
    )
    tags: Mapped[list[Tag]] = relationship(
        Tag,
        secondary=application_tags,
        lazy="selectin",
        order_by=Tag.name.asc(),
    )
