"""Structured HTTP request logging middleware.

Each request is assigned a request id (honouring an inbound ``X-Request-Id``
header, else a generated UUID) which is bound to the structlog context for
downstream log lines and echoed back on the response. The middleware emits one
structured log line per request with method, path, status, and latency in ms.
"""

from __future__ import annotations

import time
import uuid as _uuid
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

log = structlog.get_logger()

_REQUEST_ID_HEADER = "X-Request-Id"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Assign a request id and emit a single structured access log per request."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        request_id = request.headers.get(_REQUEST_ID_HEADER) or str(_uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            status_code = response.status_code if response is not None else 500
            if response is not None:
                response.headers[_REQUEST_ID_HEADER] = request_id
            log.info(
                "request",
                method=request.method,
                path=request.url.path,
                status=status_code,
                ms=elapsed_ms,
            )
            structlog.contextvars.clear_contextvars()
