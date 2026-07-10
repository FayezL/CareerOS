"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from careeros_api import __version__
from careeros_api.api.v1.routes import (
    ai,
    analytics,
    applications,
    billing,
    companies,
    contacts,
    documents,
    health,
    interviews,
    me,
    notes,
    pipeline,
    reminders,
)
from careeros_api.core.config import settings
from careeros_api.core.logging import configure_logging
from careeros_api.core.middleware import RequestLoggingMiddleware
from careeros_api.core.ratelimit import RateLimitMiddleware, rate_limit_capacity
from careeros_api.errors import register_exception_handlers


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield


def create_app() -> FastAPI:
    """Construct and configure the CareerOS FastAPI application."""
    configure_logging()

    app = FastAPI(
        title="CareerOS API",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Order matters: rate limiting sits inside request logging so that 429s are
    # still captured by the access log. Later-added middleware is outermost.
    capacity = rate_limit_capacity()
    app.add_middleware(RateLimitMiddleware, capacity=capacity, refill_per_minute=capacity)
    app.add_middleware(RequestLoggingMiddleware)

    register_exception_handlers(app)

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(me.router, prefix="/api/v1")
    app.include_router(companies.router, prefix="/api/v1")
    app.include_router(applications.router, prefix="/api/v1")
    app.include_router(pipeline.router, prefix="/api/v1")
    app.include_router(contacts.router, prefix="/api/v1")
    app.include_router(interviews.router, prefix="/api/v1")
    app.include_router(notes.router, prefix="/api/v1")
    app.include_router(documents.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    app.include_router(reminders.router, prefix="/api/v1")
    app.include_router(ai.router, prefix="/api/v1")
    app.include_router(billing.router, prefix="/api/v1")

    @app.get("/", tags=["health"])
    async def root() -> dict[str, str]:
        """Root health summary."""
        return {
            "status": "ok",
            "service": "careeros-api",
            "version": f"v{__version__}",
        }

    return app


app = create_app()
