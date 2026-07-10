"""Read-only analytics aggregation queries (all scoped by ``user_id``)."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.models.application import Application
from careeros_api.models.application_stage_history import ApplicationStageHistory
from careeros_api.models.pipeline_stage import PipelineStage


async def application_counts(session: AsyncSession, user_id: uuid.UUID) -> tuple[int, int]:
    """Return ``(total, active)`` application counts for ``user_id``."""
    total_stmt = (
        select(func.count())
        .select_from(Application)
        .where(Application.user_id == user_id, Application.deleted_at.is_(None))
    )
    active_stmt = (
        select(func.count())
        .select_from(Application)
        .where(
            Application.user_id == user_id,
            Application.deleted_at.is_(None),
            Application.status == "active",
        )
    )
    total = int((await session.execute(total_stmt)).scalar_one())
    active = int((await session.execute(active_stmt)).scalar_one())
    return total, active


async def stage_entered_counts(
    session: AsyncSession, user_id: uuid.UUID
) -> dict[uuid.UUID, tuple[int, int]]:
    """Map each ``to_stage_id`` to ``(entered_events, distinct_applications)``.

    Computed from the user's ``application_stage_history`` (joined through the
    application owner filter).
    """
    entered_stmt = (
        select(
            ApplicationStageHistory.to_stage_id,
            func.count().label("entered"),
            func.count(ApplicationStageHistory.application_id.distinct()).label(
                "distinct_applications"
            ),
        )
        .join(Application, Application.id == ApplicationStageHistory.application_id)
        .where(Application.user_id == user_id)
        .group_by(ApplicationStageHistory.to_stage_id)
    )
    result = await session.execute(entered_stmt)
    out: dict[uuid.UUID, tuple[int, int]] = {}
    for row in result.all():
        out[row.to_stage_id] = (int(row.entered), int(row.distinct_applications))
    return out


async def stages_ordered(session: AsyncSession, user_id: uuid.UUID) -> list[PipelineStage]:
    """Return the caller's stages ordered by position."""
    stmt = (
        select(PipelineStage)
        .where(PipelineStage.user_id == user_id)
        .order_by(PipelineStage.position.asc(), PipelineStage.id.asc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def applications_per_bucket(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    granularity: str,
    from_date: date,
    to_date: date,
) -> dict[str, int]:
    """Return ``{bucket_label: count}`` for applications created in the window.

    Buckets are produced by ``date_trunc`` (``"day"`` or ``"week"``) and cast to
    a calendar date; the resulting label is ``YYYY-MM-DD``.
    """
    bucket_expr = cast(func.date_trunc(granularity, Application.created_at), Date).label("bucket")
    created_date = cast(Application.created_at, Date)
    stmt = (
        select(bucket_expr, func.count().label("applications"))
        .where(
            Application.user_id == user_id,
            Application.deleted_at.is_(None),
            created_date >= from_date,
            created_date <= to_date,
        )
        .group_by(bucket_expr)
        .order_by(bucket_expr.asc())
    )
    result = await session.execute(stmt)
    return {str(row.bucket): int(row.applications) for row in result.all()}
