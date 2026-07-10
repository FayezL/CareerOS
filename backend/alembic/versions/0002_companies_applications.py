"""companies and applications tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-09 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    application_status = postgresql.ENUM(
        "active",
        "archived",
        "rejected",
        "accepted",
        name="application_status",
        create_type=False,
    )
    application_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "companies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("size", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("linkedin_url", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.Column("deleted_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_companies_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_companies")),
    )
    op.create_index(op.f("ix_companies_user_id"), "companies", ["user_id"], unique=False)
    op.create_index(
        "uq_companies_user_id_name_lower",
        "companies",
        ["user_id", sa.text("lower(name)")],
        unique=True,
    )

    op.create_table(
        "applications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_title", sa.String(), nullable=False),
        sa.Column(
            "status",
            application_status,
            nullable=False,
            server_default="active",
        ),
        sa.Column("job_url", sa.String(), nullable=True),
        sa.Column("job_description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("salary_currency", sa.String(length=3), nullable=True),
        sa.Column("applied_at", sa.Date(), nullable=True),
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
        sa.Column("deleted_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_applications_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_applications_company_id_companies"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applications")),
    )
    op.create_index(op.f("ix_applications_user_id"), "applications", ["user_id"], unique=False)
    op.create_index(
        "ix_applications_user_id_status",
        "applications",
        ["user_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_applications_user_id_applied_at",
        "applications",
        ["user_id", "applied_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_applications_company_id"), "applications", ["company_id"], unique=False
    )

    op.execute(
        """
        CREATE TRIGGER companies_set_updated_at
            BEFORE UPDATE ON companies
            FOR EACH ROW
            EXECUTE PROCEDURE set_updated_at();
        """
    )
    op.execute(
        """
        CREATE TRIGGER applications_set_updated_at
            BEFORE UPDATE ON applications
            FOR EACH ROW
            EXECUTE PROCEDURE set_updated_at();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS applications_set_updated_at ON applications")
    op.execute("DROP TRIGGER IF EXISTS companies_set_updated_at ON companies")

    op.drop_index(op.f("ix_applications_company_id"), table_name="applications")
    op.drop_index("ix_applications_user_id_applied_at", table_name="applications")
    op.drop_index("ix_applications_user_id_status", table_name="applications")
    op.drop_index(op.f("ix_applications_user_id"), table_name="applications")
    op.drop_table("applications")

    op.drop_index("uq_companies_user_id_name_lower", table_name="companies")
    op.drop_index(op.f("ix_companies_user_id"), table_name="companies")
    op.drop_table("companies")

    op.execute("DROP TYPE IF EXISTS application_status")
