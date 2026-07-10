"""Application ORM model."""

from __future__ import annotations

import uuid
from datetime import date

import sqlalchemy as sa
from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from careeros_api.db.base import Base
from careeros_api.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey
from careeros_api.models.company import Company
from careeros_api.models.pipeline_stage import PipelineStage

application_status = sa.Enum(
    "active",
    "archived",
    "rejected",
    "accepted",
    name="application_status",
    native_enum=True,
)


class Application(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """A single job application tracked by a user against a company."""

    __tablename__ = "applications"

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

    company: Mapped[Company] = relationship(
        Company,
        foreign_keys=[company_id],
        backref="applications",
    )
    current_stage: Mapped[PipelineStage | None] = relationship(
        PipelineStage,
        foreign_keys=[current_stage_id],
    )
