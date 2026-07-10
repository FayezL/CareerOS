"""Shared, generic schemas."""

from __future__ import annotations

from pydantic import BaseModel


class MessageOut(BaseModel):
    """A minimal message payload, reused for health and status responses."""

    message: str


class PageOut[T](BaseModel):
    """A single page of cursor-paginated results."""

    items: list[T]
    next_cursor: str | None = None
