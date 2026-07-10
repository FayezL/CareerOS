"""Security-related exceptions."""

from __future__ import annotations


class AuthError(Exception):
    """Raised when authentication or token verification fails."""
