"""RFC 7807 ``application/problem+json`` responses and exception handlers."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from careeros_api.core.security.errors import AuthError

log = structlog.get_logger()

_PROBLEM_MEDIA_TYPE = "application/problem+json"

_HTTP_TITLES: dict[int, str] = {
    404: "Not Found",
    405: "Method Not Allowed",
    429: "Too Many Requests",
}


class NotFoundError(Exception):
    """Raised when a requested resource does not exist (maps to HTTP 404)."""


class ConflictError(Exception):
    """Raised on a uniqueness/state conflict (maps to HTTP 409)."""


def problem(
    status_code: int,
    title: str,
    detail: str,
    *,
    type_: str = "about:blank",
    headers: dict[str, str] | None = None,
    **extra: Any,
) -> JSONResponse:
    """Build a minimal RFC 7807 problem-details response."""
    content: dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    content.update(extra)
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(content),
        media_type=_PROBLEM_MEDIA_TYPE,
        headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all problem+json exception handlers on ``app``."""

    @app.exception_handler(AuthError)
    async def handle_auth_error(_: Request, exc: AuthError) -> JSONResponse:
        return problem(
            status.HTTP_401_UNAUTHORIZED,
            "Unauthorized",
            str(exc) or "Authentication failed",
        )

    @app.exception_handler(NotFoundError)
    async def handle_not_found_error(_: Request, exc: NotFoundError) -> JSONResponse:
        return problem(
            status.HTTP_404_NOT_FOUND,
            "Not Found",
            str(exc) or "Resource not found",
        )

    @app.exception_handler(ConflictError)
    async def handle_conflict_error(_: Request, exc: ConflictError) -> JSONResponse:
        return problem(
            status.HTTP_409_CONFLICT,
            "Conflict",
            str(exc) or "Request conflicts with current state",
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return problem(
            422,
            "Validation Error",
            "One or more request fields failed validation.",
            errors=jsonable_encoder(exc.errors()),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        title = _HTTP_TITLES.get(exc.status_code, "Error")
        headers = {str(k): str(v) for k, v in exc.headers.items()} if exc.headers else None
        return problem(
            exc.status_code,
            title,
            exc.detail or title,
            headers=headers,
        )

    @app.exception_handler(Exception)
    async def handle_unhandled_error(_: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_exception", error=str(exc))
        return problem(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            "An unexpected error occurred.",
        )
