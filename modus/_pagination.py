"""
Helpers to build Page[T] / AsyncPage[T] from a raw API list response.

All list endpoints return the same shape:
    { "items": [...], "nextCursor": "string-or-null" }

Resources call build_page() (sync) or build_async_page() (async) and pass a
fetch_page callable so the Page can transparently fetch further pages without
knowing about HTTP or config.
"""

from __future__ import annotations
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type, TypeVar

from ._exceptions import ModusError
from .types.pagination import AsyncPage, Page

T = TypeVar("T")


def build_page(
    data: Dict[str, Any],
    item_class: Type[T],
    fetch_page: Callable[[str], Page[T]],
) -> Page[T]:
    """
    Construct a Page[T] from a raw list-endpoint response dict.

    Args:
        data:       Parsed JSON dict with "items" and "nextCursor" keys.
        item_class: Pydantic model class — each raw item is validated via
                    item_class.model_validate(raw).
        fetch_page: Callable(cursor) -> Page[T] used for pagination.
    """
    if not isinstance(data, dict) or "items" not in data:
        raise ModusError(
            f"Unexpected list response shape: missing 'items'. "
            f"Got: {type(data).__name__}. This is likely a backend error."
        )
    raw_items: List[Dict[str, Any]] = data.get("items", [])
    items = [item_class.model_validate(raw) for raw in raw_items]  # type: ignore[attr-defined]
    next_cursor: Optional[str] = data.get("nextCursor") or None
    return Page(items=items, next_cursor=next_cursor, _fetch_page=fetch_page)


def build_async_page(
    data: Dict[str, Any],
    item_class: Type[T],
    fetch_page: Callable[[str], Awaitable[AsyncPage[T]]],
) -> AsyncPage[T]:
    """
    Construct an AsyncPage[T] from a raw list-endpoint response dict.

    Args:
        data:       Parsed JSON dict with "items" and "nextCursor" keys.
        item_class: Pydantic model class.
        fetch_page: Async callable(cursor) -> AsyncPage[T] used for pagination.
                    Typically a bound method: lambda cur: self._list_page(limit, cur)
    """
    if not isinstance(data, dict) or "items" not in data:
        raise ModusError(
            f"Unexpected list response shape: missing 'items'. "
            f"Got: {type(data).__name__}. This is likely a backend error."
        )
    raw_items: List[Dict[str, Any]] = data.get("items", [])
    items = [item_class.model_validate(raw) for raw in raw_items]  # type: ignore[attr-defined]
    next_cursor: Optional[str] = data.get("nextCursor") or None
    return AsyncPage(items=items, next_cursor=next_cursor, _fetch_page=fetch_page)
