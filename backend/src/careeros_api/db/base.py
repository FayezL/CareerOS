"""Declarative base with an explicit naming convention for constraints."""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

naming_convention: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Project-wide declarative base.

    All ORM models inherit from this class so that Alembic autogenerate sees a
    single ``MetaData`` object, and so that constraints receive deterministic,
    convention-driven names.
    """

    metadata = MetaData(naming_convention=naming_convention)
