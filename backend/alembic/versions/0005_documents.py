"""documents table

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-12 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    document_type = postgresql.ENUM(
        "resume",
        "cover_letter",
        "other",
        name="document_type",
        create_type=False,
    )
    document_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("type", document_type, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("firebase_path", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
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
            name=op.f("fk_documents_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            name=op.f("fk_documents_application_id_applications"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
    )
    op.create_index("ix_documents_user_id_type", "documents", ["user_id", "type"], unique=False)
    op.create_index(
        op.f("ix_documents_application_id"), "documents", ["application_id"], unique=False
    )

    op.execute(
        """
        CREATE TRIGGER documents_set_updated_at
            BEFORE UPDATE ON documents
            FOR EACH ROW
            EXECUTE PROCEDURE set_updated_at();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS documents_set_updated_at ON documents")

    op.drop_index(op.f("ix_documents_application_id"), table_name="documents")
    op.drop_index("ix_documents_user_id_type", table_name="documents")
    op.drop_table("documents")

    op.execute("DROP TYPE IF EXISTS document_type")
