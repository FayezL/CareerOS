"""Repository for the ``Company`` model (all reads scoped by ``user_id``)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import ColumnExpressionArgument, select
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.models.company import Company
from careeros_api.repositories.base import BaseRepository
from careeros_api.schemas.company import CompanyCreate, CompanyUpdate


class CompanyRepository(BaseRepository[Company]):
    """Data access for companies belonging to a single user."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Company)

    async def list(  # type: ignore[override]
        self,
        user_id: uuid.UUID,
        *,
        limit: int,
        cursor: str | None = None,
        q: str | None = None,
    ) -> tuple[Sequence[Company], str | None]:
        """Page through a user's non-deleted companies, optionally filtered by name."""

        def build_filters() -> list[ColumnExpressionArgument[bool]]:
            conditions: list[ColumnExpressionArgument[bool]] = [Company.deleted_at.is_(None)]
            if q:
                conditions.append(Company.name.ilike(f"%{q}%"))
            return conditions

        return await self.list_paginated(
            user_id,
            limit=limit,
            cursor=cursor,
            filters_builder=build_filters,
        )

    async def get(self, user_id: uuid.UUID, company_id: uuid.UUID) -> Company | None:
        """Return the company if it exists, belongs to ``user_id``, and is not deleted."""
        stmt = select(Company).where(
            Company.id == company_id,
            Company.user_id == user_id,
            Company.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, data: CompanyCreate) -> Company:
        """Insert a new company owned by ``user_id``."""
        company = Company(user_id=user_id, **data.model_dump())
        self.session.add(company)
        await self.session.flush()
        await self.session.refresh(company)
        return company

    async def update(self, company: Company, data: CompanyUpdate) -> Company:
        """Apply a partial update to ``company`` using only provided fields."""
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(company, field, value)
        await self.session.flush()
        await self.session.refresh(company)
        return company

    async def soft_delete(self, company: Company) -> None:
        """Mark ``company`` as deleted without removing the row."""
        company.deleted_at = datetime.now(tz=UTC)
        await self.session.flush()
