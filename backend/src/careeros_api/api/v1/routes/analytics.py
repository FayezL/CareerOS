"""Endpoints for read-only analytics (``/api/v1/analytics``)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query

from careeros_api.api.deps import CurrentUserDep, SessionDep
from careeros_api.schemas.analytics import (
    AnalyticsFunnel,
    AnalyticsOverTime,
    AnalyticsSummary,
    Granularity,
)
from careeros_api.services import analytics as analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(
    session: SessionDep,
    current_user: CurrentUserDep,
) -> AnalyticsSummary:
    """Return headline totals and the response rate."""
    return await analytics_service.summary(session, current_user)


@router.get("/funnel", response_model=AnalyticsFunnel)
async def get_funnel(
    session: SessionDep,
    current_user: CurrentUserDep,
) -> AnalyticsFunnel:
    """Return per-stage funnel counts derived from stage history."""
    return await analytics_service.funnel(session, current_user)


@router.get("/over-time", response_model=AnalyticsOverTime)
async def get_over_time(
    session: SessionDep,
    current_user: CurrentUserDep,
    granularity: Granularity = Query("day"),
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
) -> AnalyticsOverTime:
    """Return applications created per day/week bucket within a window."""
    return await analytics_service.over_time(
        session,
        current_user,
        granularity=granularity,
        from_date=from_date,
        to_date=to_date,
    )
