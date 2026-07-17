"""keyset pagination indexes

Adds (user_id, created_at DESC, id DESC) composite indexes to the tables that
use ``BaseRepository.list_paginated``. Without these, the generic keyset
query (ORDER BY created_at DESC, id DESC LIMIT n) had to materialize and
in-memory sort every row owned by the user before applying LIMIT. With them,
the planner walks the index in order and stops at LIMIT -> O(limit) instead
of O(n log n). ``notes`` already has (user_id, created_at) so it is omitted.

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-18 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# (table, index_name) for every table using list_paginated except notes.
_TARGETS: list[tuple[str, str]] = [
    ("companies", "ix_companies_user_id_created_at_id"),
    ("applications", "ix_applications_user_id_created_at_id"),
    ("contacts", "ix_contacts_user_id_created_at_id"),
    ("documents", "ix_documents_user_id_created_at_id"),
    ("interviews", "ix_interviews_user_id_created_at_id"),
    ("reminders", "ix_reminders_user_id_created_at_id"),
]

_COLUMNS = [sa.text("user_id"), sa.text("created_at DESC"), sa.text("id DESC")]


def upgrade() -> None:
    for table, name in _TARGETS:
        op.create_index(name, table, _COLUMNS, unique=False)


def downgrade() -> None:
    for table, name in reversed(_TARGETS):
        op.drop_index(name, table_name=table)
