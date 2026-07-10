"""Analytics business-logic services (read-only, user-scoped)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from careeros_api.models.user import User
from careeros_api.repositories import analytics as analytics_repo
from careeros_api.schemas.analytics import (
    AnalyticsFunnel,
    AnalyticsOverTime,
    AnalyticsSummary,
    FunnelStageCount,
    SummaryTotals,
    TimeBucket,
)

_INTERVIEW_STAGE_NAMES = {"interview"}
_OFFER_STAGE_NAMES = {"offer"}


async def summary(session: AsyncSession, user: User) -> AnalyticsSummary:
    """Compute headline totals and the response rate.

    ``response_rate = (interviews + offers) / applications`` where
    ``interviews``/``offers`` are distinct applications that have ever entered a
    stage named "Interview"/"Offer".
    """
    total, active = await analytics_repo.application_counts(session, user.id)
    entered = await analytics_repo.stage_entered_counts(session, user.id)
    stages = await analytics_repo.stages_ordered(session, user.id)

    name_by_id = {stage.id: stage.name for stage in stages}
    interviews = 0
    offers = 0
    for stage_id, (_entered_events, distinct_apps) in entered.items():
        name = (name_by_id.get(stage_id) or "").lower()
        if name in _INTERVIEW_STAGE_NAMES:
            interviews += distinct_apps
        elif name in _OFFER_STAGE_NAMES:
            offers += distinct_apps

    response_rate = (interviews + offers) / total if total else 0.0

    return AnalyticsSummary(
        generated_at=datetime.now(tz=UTC),
        totals=SummaryTotals(
            applications=total,
            active=active,
            interviews=interviews,
            offers=offers,
        ),
        response_rate=round(response_rate, 3),
    )


async def funnel(session: AsyncSession, user: User) -> AnalyticsFunnel:
    """Compute per-stage funnel counts from stage history."""
    entered = await analytics_repo.stage_entered_counts(session, user.id)
    stages = await analytics_repo.stages_ordered(session, user.id)

    counts: list[FunnelStageCount] = []
    for stage in stages:
        entered_events, distinct_apps = entered.get(stage.id, (0, 0))
        counts.append(
            FunnelStageCount(
                stage_id=stage.id,
                name=stage.name,
                position=stage.position,
                entered=entered_events,
                distinct_applications=distinct_apps,
            )
        )
    return AnalyticsFunnel(generated_at=datetime.now(tz=UTC), stages=counts)


async def over_time(
    session: AsyncSession,
    user: User,
    *,
    granularity: str,
    from_date: date,
    to_date: date,
) -> AnalyticsOverTime:
    """Compute applications created per day/week bucket within ``[from, to]``.

    Buckets are emitted contiguously so days/weeks with zero applications still
    appear in the response.
    """
    raw = await analytics_repo.applications_per_bucket(
        session,
        user.id,
        granularity=granularity,
        from_date=from_date,
        to_date=to_date,
    )
    buckets: list[TimeBucket] = []
    cursor = _bucket_start(from_date, granularity)
    end = _bucket_start(to_date, granularity)
    while cursor <= end:
        label = cursor.isoformat()
        buckets.append(TimeBucket(bucket=label, applications=raw.get(label, 0)))
        cursor = _advance(cursor, granularity)
    return AnalyticsOverTime.model_validate(
        {
            "generated_at": datetime.now(tz=UTC),
            "granularity": granularity,
            "from": from_date,
            "to": to_date,
            "buckets": buckets,
        }
    )


def _bucket_start(d: date, granularity: str) -> date:
    """Align ``d`` to the start of its bucket (week -> Monday)."""
    if granularity == "week":
        return d - timedelta(days=d.weekday())
    return d


def _advance(d: date, granularity: str) -> date:
    return d + (timedelta(days=1) if granularity == "day" else timedelta(weeks=1))
