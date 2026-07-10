"""Company business-logic services."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.errors import NotFoundError
from careeros_api.models.user import User
from careeros_api.repositories.company import CompanyRepository
from careeros_api.schemas.common import PageOut
from careeros_api.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate


async def list_companies(
    session: AsyncSession,
    user: User,
    *,
    limit: int,
    cursor: str | None,
    q: str | None,
) -> PageOut[CompanyRead]:
    """Return one page of the caller's companies."""
    repo = CompanyRepository(session)
    items, next_cursor = await repo.list(user.id, limit=limit, cursor=cursor, q=q)
    return PageOut(items=[CompanyRead.model_validate(c) for c in items], next_cursor=next_cursor)


async def get_company(session: AsyncSession, user: User, company_id: uuid.UUID) -> CompanyRead:
    """Return a single company owned by the caller."""
    repo = CompanyRepository(session)
    company = await repo.get(user.id, company_id)
    if company is None:
        raise NotFoundError(f"Company {company_id} not found")
    return CompanyRead.model_validate(company)


async def create_company(session: AsyncSession, user: User, data: CompanyCreate) -> CompanyRead:
    """Create a new company for the caller."""
    repo = CompanyRepository(session)
    company = await repo.create(user.id, data)
    return CompanyRead.model_validate(company)


async def update_company(
    session: AsyncSession,
    user: User,
    company_id: uuid.UUID,
    data: CompanyUpdate,
) -> CompanyRead:
    """Partially update a company owned by the caller."""
    repo = CompanyRepository(session)
    company = await repo.get(user.id, company_id)
    if company is None:
        raise NotFoundError(f"Company {company_id} not found")
    updated = await repo.update(company, data)
    return CompanyRead.model_validate(updated)


async def delete_company(session: AsyncSession, user: User, company_id: uuid.UUID) -> None:
    """Soft-delete a company owned by the caller."""
    repo = CompanyRepository(session)
    company = await repo.get(user.id, company_id)
    if company is None:
        raise NotFoundError(f"Company {company_id} not found")
    await repo.soft_delete(company)
