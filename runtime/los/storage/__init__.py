"""Storage module — local JSON persistence for user data."""

from los.storage.adapter import exists, load, save

__all__ = [
    "exists",
    "load",
    "save",
]

