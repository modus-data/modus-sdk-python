"""Small helpers for building request URLs."""
from __future__ import annotations

from typing import Optional
from urllib.parse import quote


def _validate_update_mask(update_mask: str) -> None:
    if not update_mask.strip():
        raise ValueError(
            "update_mask must be a non-empty comma-separated list of field names"
        )


def update_mask_query(update_mask: Optional[str]) -> Optional[dict[str, str]]:
    """Build an ``updateMask`` query dict for PATCH via ``invoke_operation``."""
    if update_mask is None:
        return None
    _validate_update_mask(update_mask)
    return {"updateMask": update_mask}


def with_update_mask(path: str, update_mask: Optional[str]) -> str:
    """Append an ``updateMask`` query parameter to ``path`` when provided.

    The API uses ``updateMask`` (a comma-separated list of field names) on PATCH
    requests to explicitly clear fields. When ``update_mask`` is ``None`` the path
    is returned unchanged.

    Raises:
        ValueError: If ``update_mask`` is given but empty or whitespace-only — an
            empty ``updateMask=`` query value has ambiguous PATCH semantics.
    """
    if update_mask is None:
        return path
    _validate_update_mask(update_mask)
    sep = "&" if "?" in path else "?"
    return f"{path}{sep}updateMask={quote(update_mask, safe='')}"
