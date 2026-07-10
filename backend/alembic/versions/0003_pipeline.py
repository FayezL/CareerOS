"""pipeline stages and application stage history

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-10 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pipeline_stages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(), nullable=True),
        sa.Column(
            "is_default",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_pipeline_stages_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pipeline_stages")),
        sa.UniqueConstraint(
            "user_id",
            "position",
            name="uq_pipeline_stages_user_id_position",
        ),
    )
    op.create_index(
        op.f("ix_pipeline_stages_user_id"), "pipeline_stages", ["user_id"], unique=False
    )

    op.create_table(
        "application_stage_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_stage_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("to_stage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "changed_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            name=op.f("fk_application_stage_history_application_id_applications"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["from_stage_id"],
            ["pipeline_stages.id"],
            name=op.f("fk_application_stage_history_from_stage_id_pipeline_stages"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["to_stage_id"],
            ["pipeline_stages.id"],
            name=op.f("fk_application_stage_history_to_stage_id_pipeline_stages"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_application_stage_history")),
    )
    op.create_index(
        op.f("ix_application_stage_history_application_id"),
        "application_stage_history",
        ["application_id"],
        unique=False,
    )
    op.create_index(
        "ix_application_stage_history_application_id_changed_at",
        "application_stage_history",
        ["application_id", "changed_at"],
        unique=False,
    )

    op.add_column(
        "applications",
        sa.Column("current_stage_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_applications_current_stage_id_pipeline_stages"),
        "applications",
        "pipeline_stages",
        ["current_stage_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        op.f("ix_applications_current_stage_id"),
        "applications",
        ["current_stage_id"],
        unique=False,
    )

    op.execute(
        """
        CREATE TRIGGER pipeline_stages_set_updated_at
            BEFORE UPDATE ON pipeline_stages
            FOR EACH ROW
            EXECUTE PROCEDURE set_updated_at();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS pipeline_stages_set_updated_at ON pipeline_stages")

    op.drop_index(op.f("ix_applications_current_stage_id"), table_name="applications")
    op.drop_constraint(
        op.f("fk_applications_current_stage_id_pipeline_stages"),
        "applications",
        type_="foreignkey",
    )
    op.drop_column("applications", "current_stage_id")

    op.drop_index(
        "ix_application_stage_history_application_id_changed_at",
        table_name="application_stage_history",
    )
    op.drop_index(
        op.f("ix_application_stage_history_application_id"),
        table_name="application_stage_history",
    )
    op.drop_table("application_stage_history")

    op.drop_index(op.f("ix_pipeline_stages_user_id"), table_name="pipeline_stages")
    op.drop_table("pipeline_stages")
