"""Document versioning: type expansion, grouping, version labels.

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-24

Downgrade drops the new columns/indexes but deliberately does NOT shrink
the document_type enum (Postgres cannot remove enum values without
recreating the type; extra unused values are harmless).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

GROUP_KEY = sa.text("COALESCE(parent_document_id, id)")


def upgrade() -> None:
    # ADD VALUE cannot run inside a transaction on some setups — use an
    # autocommit block so behaviour is deterministic.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE document_type ADD VALUE IF NOT EXISTS 'certificate'")
        op.execute("ALTER TYPE document_type ADD VALUE IF NOT EXISTS 'reference'")
        op.execute("ALTER TYPE document_type ADD VALUE IF NOT EXISTS 'visa'")

    op.add_column(
        "documents",
        sa.Column("parent_document_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_documents_parent_document_id",
        "documents",
        "documents",
        ["parent_document_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.add_column("documents", sa.Column("version_label", sa.String(255), nullable=True))
    op.add_column(
        "documents",
        sa.Column(
            "is_latest_version",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    op.create_index(
        "ix_documents_user_type_created_at",
        "documents",
        ["user_id", "type", sa.text("created_at DESC"), sa.text("id DESC")],
    )
    op.create_index("ix_documents_parent_document_id", "documents", ["parent_document_id"])
    op.create_index(
        "ix_documents_one_latest_per_group",
        "documents",
        [GROUP_KEY],
        unique=True,
        postgresql_where=sa.text("is_latest_version = true"),
    )
    op.create_index(
        "ix_documents_group_version",
        "documents",
        [GROUP_KEY, sa.text("version")],
        unique=True,
    )
    op.drop_index("ix_documents_user_id_type", table_name="documents")


def downgrade() -> None:
    op.create_index(
        "ix_documents_user_id_type",
        "documents",
        ["user_id", "type"],
    )
    op.drop_index("ix_documents_group_version", table_name="documents")
    op.drop_index("ix_documents_one_latest_per_group", table_name="documents")
    op.drop_index("ix_documents_parent_document_id", table_name="documents")
    op.drop_index("ix_documents_user_type_created_at", table_name="documents")
    op.drop_constraint("fk_documents_parent_document_id", "documents", type_="foreignkey")
    op.drop_column("documents", "is_latest_version")
    op.drop_column("documents", "version_label")
    op.drop_column("documents", "parent_document_id")
    # document_type enum is intentionally NOT shrunk (see module docstring).
