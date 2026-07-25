"""Shared utilities with zero internal dependencies.

This module MUST NOT import from any other los sub-package.
It exists solely to hold functions used by multiple layers
without violating dependency direction rules.
"""

from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()
