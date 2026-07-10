"""Health-check endpoints (liveness + readiness)."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from structlog import get_logger

from careeros_api.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])
log = get_logger()


@router.get("")
async def liveness() -> dict[str, str]:
    """Liveness probe — does not touch the database."""
    return {"status": "ok", "env": settings.ENV}


@router.get("/ready")
async def readiness() -> JSONResponse:
    """Readiness probe — verifies the database is reachable via ``SELECT 1``."""
    return await _check_readiness()


async def _check_readiness() -> JSONResponse:
    # Use a self-contained session so a database outage cannot break the
    # request lifecycle of the shared ``get_session`` dependency.
    from careeros_api.db.session import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - any failure means "not ready"
        log.warning("readiness_check_failed", error=str(exc))
        return JSONResponse(
            status_code=503,
            content={"status": "degraded"},
        )
    return JSONResponse(status_code=200, content={"status": "ok"})


__all__ = ["router"]
