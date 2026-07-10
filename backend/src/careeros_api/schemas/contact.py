"""Contact request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactBase(BaseModel):
    """Fields shared across contact create/read schemas."""

    company_id: uuid.UUID | None = None
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=64)
    linkedin_url: str | None = Field(default=None, max_length=2048)
    role_title: str | None = Field(default=None, max_length=255)


class ContactCreate(ContactBase):
    """Payload to create a contact (all identity fields optional)."""


class ContactUpdate(BaseModel):
    """Partial update for a contact; every field is optional."""

    company_id: uuid.UUID | None = None
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=64)
    linkedin_url: str | None = Field(default=None, max_length=2048)
    role_title: str | None = Field(default=None, max_length=255)


class ContactRead(BaseModel):
    """Public representation of a contact."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID | None
    first_name: str | None
    last_name: str | None
    email: EmailStr | None
    phone: str | None
    linkedin_url: str | None
    role_title: str | None
    created_at: datetime
    updated_at: datetime
