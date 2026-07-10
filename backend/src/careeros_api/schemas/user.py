"""User request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRead(BaseModel):
    """The public representation of a user."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clerk_user_id: str
    email: EmailStr
    full_name: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """A partial update for the authenticated user's mutable fields."""

    full_name: str | None = None
    avatar_url: str | None = None
