"""Tiny client-side validators shared across resources.

These exist so we fail fast on obvious bad inputs (empty IDs, negative limits)
before making a network call. They raise ``ValueError`` — caller-visible bugs,
not server-side conditions.
"""
from __future__ import annotations
from typing import Union


def validate_limit(limit: int) -> None:
    """Reject limit values that the backend would reject anyway, locally."""
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError(f"limit must be a positive int, got {limit!r}")


def validate_id(resource_id: Union[int, str], *, name: str = "id") -> None:
    """Reject empty/whitespace-only string IDs that would produce ambiguous URLs."""
    if isinstance(resource_id, str) and not resource_id.strip():
        raise ValueError(f"{name} must be a non-empty string or int")
