"""Endpoints for the authenticated user's companies (``/api/v1/companies``)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Response, status

from careeros_api.api.deps import CurrentUserDep, SessionDep
from careeros_api.schemas.common import PageOut
from careeros_api.schemas.company import (
    CompanyCreate,
    CompanyOption,
    CompanyRead,
    CompanyUpdate,
)
from careeros_api.services import company as company_service

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=PageOut[CompanyRead])
async def list_companies(
    session: SessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    q: str | None = Query(None),
) -> PageOut[CompanyRead]:
    """Page through the caller's companies."""
    return await company_service.list_companies(
        session, current_user, limit=limit, cursor=cursor, q=q
    )


@router.get("/search", response_model=list[CompanyOption])
async def search_companies(
    session: SessionDep,
    current_user: CurrentUserDep,
    q: str = Query(..., min_length=1, max_length=255),
    limit: int = Query(8, ge=1, le=20),
) -> list[CompanyOption]:
    """Prefix-match autocomplete for the company picker on the application form."""
    return await company_service.search_companies(session, current_user, q=q, limit=limit)


@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
async def create_company(
    session: SessionDep,
    current_user: CurrentUserDep,
    data: CompanyCreate,
) -> CompanyRead:
    """Create a new company for the caller."""
    return await company_service.create_company(session, current_user, data)


@router.get("/{company_id}", response_model=CompanyRead)
async def get_company(
    session: SessionDep,
    current_user: CurrentUserDep,
    company_id: uuid.UUID,
) -> CompanyRead:
    """Return a single company owned by the caller."""
    return await company_service.get_company(session, current_user, company_id)


@router.patch("/{company_id}", response_model=CompanyRead)
async def update_company(
    session: SessionDep,
    current_user: CurrentUserDep,
    company_id: uuid.UUID,
    data: CompanyUpdate,
) -> CompanyRead:
    """Partially update a company owned by the caller."""
    return await company_service.update_company(session, current_user, company_id, data)


@router.delete("/{company_id}")
async def delete_company(
    session: SessionDep,
    current_user: CurrentUserDep,
    company_id: uuid.UUID,
) -> Response:
    """Soft-delete a company owned by the caller."""
    await company_service.delete_company(session, current_user, company_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
