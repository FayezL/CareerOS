"""timeline event enrichment: enum, importance, follow-up, source, summary rename

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-27 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


timeline_event_type = postgresql.ENUM(
    "APPLIED",
    "EMAIL",
    "CALL",
    "FOLLOW_UP",
    "PHONE_SCREEN",
    "TECHNICAL",
    "SYSTEM_DESIGN",
    "ONSITE",
    "TAKE_HOME",
    "RECRUITER_MESSAGE",
    "OFFER",
    "ACCEPTED",
    "REJECTED",
    "NOTE",
    "CUSTOM",
    name="timeline_event_type",
)

timeline_importance = postgresql.ENUM(
    "NORMAL",
    "IMPORTANT",
    "MILESTONE",
    name="timeline_importance",
)


def upgrade() -> None:
    timeline_event_type.create(op.get_bind(), checkfirst=False)
    timeline_importance.create(op.get_bind(), checkfirst=False)

    op.alter_column(
        "timeline_events",
        "event_type",
        type_=timeline_event_type,
        postgresql_using="event_type::text::timeline_event_type",
        existing_type=sa.String(length=64),
        existing_nullable=False,
    )

    op.alter_column("timeline_events", "title", new_column_name="summary")

    op.add_column(
        "timeline_events",
        sa.Column(
            "importance",
            timeline_importance,
            nullable=False,
            server_default="NORMAL",
        ),
    )
    op.add_column(
        "timeline_events",
        sa.Column("follow_up_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "timeline_events",
        sa.Column(
            "source",
            sa.String(length=32),
            nullable=False,
            server_default="user",
        ),
    )


def downgrade() -> None:
    op.drop_column("timeline_events", "source")
    op.drop_column("timeline_events", "follow_up_date")
    op.drop_column("timeline_events", "importance")

    op.alter_column("timeline_events", "summary", new_column_name="title")

    op.alter_column(
        "timeline_events",
        "event_type",
        type_=sa.String(length=64),
        postgresql_using="event_type::text",
        existing_type=timeline_event_type,
        existing_nullable=False,
    )

    timeline_importance.drop(op.get_bind(), checkfirst=False)
    timeline_event_type.drop(op.get_bind(), checkfirst=False)
