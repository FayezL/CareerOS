"""Notification abstraction for reminder dispatch.

* ``LogNotifier`` — always available; logs each reminder (the default/test path).
* ``EmailNotifier`` — stub selected when SMTP host configuration is present.

Both implement the ``Notifier`` interface; ``get_notifier()`` selects one based
on settings so that production wiring can be swapped without code changes.
"""

from __future__ import annotations

import structlog

from careeros_api.core.config import settings

log = structlog.get_logger()


class Notifier:
    """Abstract interface for sending a reminder notification."""

    async def send(
        self,
        *,
        to: str | None,
        title: str,
        due_at: object,
        detail: str | None = None,
    ) -> None:
        raise NotImplementedError


class LogNotifier(Notifier):
    """Logs each dispatched reminder (default / development notifier)."""

    async def send(
        self,
        *,
        to: str | None,
        title: str,
        due_at: object,
        detail: str | None = None,
    ) -> None:
        log.info(
            "reminder_dispatched",
            to=to,
            title=title,
            due_at=str(due_at),
            detail=detail,
        )


class EmailNotifier(Notifier):
    """Stub email notifier.

    A real implementation would hand off to an SMTP/SES client; for now it logs
    the would-be send so the dispatch flow can be exercised end-to-end.
    """

    async def send(
        self,
        *,
        to: str | None,
        title: str,
        due_at: object,
        detail: str | None = None,
    ) -> None:
        log.info(
            "reminder_email_queued",
            to=to,
            title=title,
            due_at=str(due_at),
            detail=detail,
        )


def get_notifier() -> Notifier:
    """Return the configured notifier (``EmailNotifier`` when SMTP host is set)."""
    if getattr(settings, "SMTP_HOST", None):
        return EmailNotifier()
    return LogNotifier()
