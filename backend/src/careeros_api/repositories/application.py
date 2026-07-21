"""Repository for the ``Application`` model (all reads scoped by ``user_id``)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import ColumnExpressionArgument, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from careeros_api.models.application import Application
from careeros_api.models.application_stage_history import ApplicationStageHistory
from careeros_api.repositories.base import BaseRepository
from careeros_api.schemas.application import ApplicationCreate, ApplicationUpdate


class ApplicationRepository(BaseRepository[Application]):
    """Data access for applications belonging to a single user."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Application)

    async def list(  # type: ignore[override]
        self,
        user_id: uuid.UUID,
        *,
        limit: int,
        cursor: str | None = None,
        status: str | None = None,
        company_id: uuid.UUID | None = None,
        q: str | None = None,
    ) -> tuple[Sequence[Application], str | None]:
        """Page through a user's non-deleted applications with optional filters."""

        def build_filters() -> list[ColumnExpressionArgument[bool]]:
            conditions: list[ColumnExpressionArgument[bool]] = [Application.deleted_at.is_(None)]
            if status is not None:
                conditions.append(Application.status == status)
            if company_id is not None:
                conditions.append(Application.company_id == company_id)
            if q:
                conditions.append(Application.role_title.ilike(f"%{q}%"))
            return conditions

        return await self.list_paginated(
            user_id,
            limit=limit,
            cursor=cursor,
            filters_builder=build_filters,
            options=[
                selectinload(Application.company),
                selectinload(Application.current_stage),
                selectinload(Application.tags),
            ],
        )

    async def get(self, user_id: uuid.UUID, application_id: uuid.UUID) -> Application | None:
        """Return the application if it exists, belongs to ``user_id``, and is not deleted."""
        stmt = (
            select(Application)
            .options(
                selectinload(Application.company),
                selectinload(Application.current_stage),
                selectinload(Application.tags),
            )
            .where(
                Application.id == application_id,
                Application.user_id == user_id,
                Application.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_company(
        self, user_id: uuid.UUID, application_id: uuid.UUID
    ) -> Application | None:
        """Return an application with its company eager-loaded (alias of :meth:`get`)."""
        return await self.get(user_id, application_id)

    async def create(
        self,
        user_id: uuid.UUID,
        data: ApplicationCreate,
        *,
        company_id: uuid.UUID,
    ) -> Application:
        """Insert a new application owned by ``user_id``.

        ``company_id`` is passed explicitly (rather than read from ``data``)
        because the service resolves it from either ``company_id`` or a
        newly-created / reused-by-name company. The carrier fields
        ``company_id`` / ``company_name`` are excluded from the dump since they
        are not Application columns.
        """
        payload = data.model_dump(exclude={"company_id", "company_name", "tags"})
        application = Application(user_id=user_id, company_id=company_id, **payload)
        self.session.add(application)
        await self.session.flush()
        return await self._reload(application.id)

    async def update(self, application: Application, data: ApplicationUpdate) -> Application:
        """Apply a partial update to ``application`` using only provided fields."""
        # `tags` (resolved by the service via the relationship) and
        # `company_name` (carrier field handled by the service) are not
        # Application columns and must be excluded from the setattr dump.
        payload = data.model_dump(
            exclude_unset=True,
            exclude={"tags", "company_name"},
        )
        for field, value in payload.items():
            setattr(application, field, value)
        await self.session.flush()
        return await self._reload(application.id)

    async def soft_delete(self, application: Application) -> None:
        """Mark ``application`` as deleted without removing the row."""
        application.deleted_at = datetime.now(tz=UTC)
        await self.session.flush()

    async def move(
        self,
        application: Application,
        to_stage_id: uuid.UUID,
        note: str | None,
    ) -> Application:
        """Append a stage-transition record and set the application's current stage."""
        from_stage_id = application.current_stage_id
        application.current_stage_id = to_stage_id
        self.session.add(
            ApplicationStageHistory(
                application_id=application.id,
                from_stage_id=from_stage_id,
                to_stage_id=to_stage_id,
                note=note,
            )
        )
        await self.session.flush()
        return await self._reload(application.id)

    async def history(self, application: Application) -> Sequence[ApplicationStageHistory]:
        """Return the stage-transition timeline for ``application`` (oldest first)."""
        stmt = (
            select(ApplicationStageHistory)
            .options(
                selectinload(ApplicationStageHistory.from_stage),
                selectinload(ApplicationStageHistory.to_stage),
            )
            .where(ApplicationStageHistory.application_id == application.id)
            .order_by(
                ApplicationStageHistory.changed_at.asc(),
                ApplicationStageHistory.id.asc(),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def _reload(self, application_id: uuid.UUID) -> Application:
        """Re-fetch an application with its relations eager-loaded."""
        stmt = (
            select(Application)
            .options(
                selectinload(Application.company),
                selectinload(Application.current_stage),
                selectinload(Application.tags),
            )
            .where(Application.id == application_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
