"""Structured logging configuration (structlog)."""

from __future__ import annotations

import logging

import structlog

from careeros_api.core.config import settings


def configure_logging() -> None:
    """Configure root logging and structlog processors."""
    logging.basicConfig(
        level=settings.LOG_LEVEL.upper(),
        format="%(message)s",
    )

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        ),
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
