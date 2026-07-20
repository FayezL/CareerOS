"""application foundation: tags, timeline events, rejection reasons

Adds three additive capabilities that the rest of the redesign builds on:

* ``tags`` + ``application_tags`` — user-scoped tags with a many-to-many join
  to applications, used for filtering and analytics (Remote, Visa Sponsorship,
  Python, Europe, …). Unique per (user, lower(name)).
* ``timeline_events`` — free-form activity log per application (recruiter
  viewed, email sent, phone screen, take-home, custom …) **alongside** the
  existing ``application_stage_history``. ``event_type`` is a plain string so
  custom user-defined types are first-class.
* ``rejection_reason`` / ``rejection_reason_category`` columns on
  ``applications`` — captured when an application is rejected, surfaced in the
  timeline and in analytics.

All three are additive; no existing column or constraint is touched.

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-19 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Native enum: rejection_reason_category. Native (not a CHECK) to match the
# codebase convention (application_status, interview_type, document_type).
rejection_reason_category = postgresql.ENUM(
    "visa_sponsorship",
    "lack_of_experience",
    "salary",
    "culture_fit",
    "position_filled",
    "no_feedback",
    "other",
    name="rejection_reason_category",
)


def upgrade() -> None:
    # --- tags -------------------------------------------------------------
    op.create_table(
        "tags",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("color", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Unique per (user, case-insensitive name). Index (not UniqueConstraint) so
    # the functional lower(name) expression matches the ORM declaration.
    op.create_index(
        "uq_tags_user_id_name_lower",
        "tags",
        ["user_id", sa.text("lower(name)")],
        unique=True,
    )
    op.create_index("ix_tags_user_id", "tags", ["user_id"], unique=False)

    # --- application_tags (many-to-many) ----------------------------------
    op.create_table(
        "application_tags",
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tag_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tags.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("application_id", "tag_id"),
    )
    # Reverse lookup: "all applications with this tag".
    op.create_index(
        "ix_application_tags_tag_id",
        "application_tags",
        ["tag_id"],
        unique=False,
    )

    # --- timeline_events --------------------------------------------------
    op.create_table(
        "timeline_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Plain string (not an enum): the spec calls for custom user-defined
        # event types beyond the predefined set.
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Per-application timeline (newest first) — the hot read path.
    op.create_index(
        "ix_timeline_events_application_id_occurred_at",
        "timeline_events",
        [sa.text("application_id"), sa.text("occurred_at DESC"), sa.text("id DESC")],
        unique=False,
    )
    # Cross-application activity feed ("recent activity" on the dashboard).
    op.create_index(
        "ix_timeline_events_user_id_occurred_at",
        "timeline_events",
        [sa.text("user_id"), sa.text("occurred_at DESC")],
        unique=False,
    )

    # --- applications: rejection columns ----------------------------------
    rejection_reason_category.create(op.get_bind(), checkfirst=False)
    op.add_column(
        "applications",
        sa.Column("rejection_reason", sa.String(255), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("rejection_reason_category", rejection_reason_category, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("applications", "rejection_reason_category")
    op.drop_column("applications", "rejection_reason")
    rejection_reason_category.drop(op.get_bind(), checkfirst=False)

    op.drop_index("ix_timeline_events_user_id_occurred_at", table_name="timeline_events")
    op.drop_index("ix_timeline_events_application_id_occurred_at", table_name="timeline_events")
    op.drop_table("timeline_events")

    op.drop_index("ix_application_tags_tag_id", table_name="application_tags")
    op.drop_table("application_tags")

    op.drop_index("ix_tags_user_id", table_name="tags")
    op.drop_table("tags")
