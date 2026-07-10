"""Analytics request/response schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Granularity = Literal["day", "week"]


class SummaryTotals(BaseModel):
    """Headline count totals."""

    applications: int
    active: int
    interviews: int
    offers: int


class AnalyticsSummary(BaseModel):
    """Aggregated headline metrics for the caller."""

    generated_at: datetime
    totals: SummaryTotals
    response_rate: float


class FunnelStageCount(BaseModel):
    """Per-stage funnel counts."""

    stage_id: uuid.UUID
    name: str
    position: int
    entered: int
    distinct_applications: int


class AnalyticsFunnel(BaseModel):
    """Stage-by-stage conversion counts derived from stage history."""

    generated_at: datetime
    stages: list[FunnelStageCount]


class TimeBucket(BaseModel):
    """A single time bucket and its application count."""

    bucket: str
    applications: int


class AnalyticsOverTime(BaseModel):
    """Applications created per time bucket within a window."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    generated_at: datetime
    granularity: Granularity
    from_: date = Field(alias="from")
    to: date
    buckets: list[TimeBucket]
