"""
Helpers to build Page[T] / AsyncPage[T] from Modus API list responses.

Public list endpoints return resource-plural arrays and ``nextPageToken``:
    { "scopes": [...], "nextPageToken": "..." }

Query params use ``pageSize`` and ``pageToken``. Python resources expose
``page_size`` / ``page_token``; ``Page.next_page_token`` maps from ``nextPageToken``.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, List, Optional, Type, TypeVar

from ._exceptions import ModusError
from .types.pagination import AsyncPage, Page

T = TypeVar("T")


def normalize_page_token(token: Optional[str]) -> Optional[str]:
    """Treat None and blank strings as no page token."""
    if token is None or not str(token).strip():
        return None
    return token


def aip_list_params(
    page_size: int,
    page_token: Optional[str] = None,
    **extra: Any,
) -> Dict[str, Any]:
    """Build cursor-pagination query params (pageSize, pageToken) plus optional filters."""
    params: Dict[str, Any] = {"pageSize": page_size, **extra}
    token = normalize_page_token(page_token)
    if token is not None:
        params["pageToken"] = token
    return params


def _next_page_token_from_response(data: Dict[str, Any]) -> Optional[str]:
    return normalize_page_token(data.get("nextPageToken"))


def resolve_list_items_key(
    data: Any, preferred: str, fallback: str
) -> str:
    """Return ``preferred`` when its value is a list; else ``fallback`` if that is a list.

    When neither key holds a list, returns ``preferred`` so downstream builders
    raise a clear error for the canonical envelope key.
    """
    if not isinstance(data, dict):
        raise ModusError(
            f"Unexpected list response shape: expected an object, "
            f"got {type(data).__name__}. This is likely a backend error."
        )
    if isinstance(data.get(preferred), list):
        return preferred
    if isinstance(data.get(fallback), list):
        return fallback
    return preferred


def _require_items_list(data: Dict[str, Any], items_key: str) -> List[Any]:
    """Return ``data[items_key]`` when it is a list; otherwise raise ModusError."""
    value = data.get(items_key)
    if not isinstance(value, list):
        raise ModusError(
            f"Unexpected list response shape: {items_key!r} must be a list, "
            f"got {type(value).__name__}. This is likely a backend error."
        )
    return value


def build_aip_page(
    data: Dict[str, Any],
    items_key: str,
    item_class: Type[T],
    fetch_page: Callable[[str], Page[T]],
) -> Page[T]:
    """Construct Page[T] from an AIP list response with a Pydantic item class."""
    if not isinstance(data, dict) or items_key not in data:
        raise ModusError(
            f"Unexpected list response shape: missing {items_key!r}. "
            f"Got: {type(data).__name__}. This is likely a backend error."
        )
    raw_items: List[Dict[str, Any]] = _require_items_list(data, items_key)
    items = [item_class.model_validate(raw) for raw in raw_items]  # type: ignore[attr-defined]
    return Page(
        items=items,
        next_page_token=_next_page_token_from_response(data),
        _fetch_page=fetch_page,
    )


def build_async_aip_page(
    data: Dict[str, Any],
    items_key: str,
    item_class: Type[T],
    fetch_page: Callable[[str], Awaitable[AsyncPage[T]]],
) -> AsyncPage[T]:
    """Construct AsyncPage[T] from an AIP list response with a Pydantic item class."""
    if not isinstance(data, dict) or items_key not in data:
        raise ModusError(
            f"Unexpected list response shape: missing {items_key!r}. "
            f"Got: {type(data).__name__}. This is likely a backend error."
        )
    raw_items: List[Dict[str, Any]] = _require_items_list(data, items_key)
    items = [item_class.model_validate(raw) for raw in raw_items]  # type: ignore[attr-defined]
    return AsyncPage(
        items=items,
        next_page_token=_next_page_token_from_response(data),
        _fetch_page=fetch_page,
    )


def build_aip_page_mapped(
    data: Dict[str, Any],
    items_key: str,
    map_item: Callable[[Dict[str, Any]], T],
    fetch_page: Callable[[str], Page[T]],
) -> Page[T]:
    """Construct Page[T] from an AIP list response using a per-item mapper."""
    if not isinstance(data, dict) or items_key not in data:
        raise ModusError(
            f"Unexpected list response shape: missing {items_key!r}. "
            f"Got: {type(data).__name__}. This is likely a backend error."
        )
    raw_items: List[Dict[str, Any]] = _require_items_list(data, items_key)
    items = [map_item(raw) for raw in raw_items]
    return Page(
        items=items,
        next_page_token=_next_page_token_from_response(data),
        _fetch_page=fetch_page,
    )


def build_async_aip_page_mapped(
    data: Dict[str, Any],
    items_key: str,
    map_item: Callable[[Dict[str, Any]], T],
    fetch_page: Callable[[str], Awaitable[AsyncPage[T]]],
) -> AsyncPage[T]:
    """Construct AsyncPage[T] from an AIP list response using a per-item mapper."""
    if not isinstance(data, dict) or items_key not in data:
        raise ModusError(
            f"Unexpected list response shape: missing {items_key!r}. "
            f"Got: {type(data).__name__}. This is likely a backend error."
        )
    raw_items: List[Dict[str, Any]] = _require_items_list(data, items_key)
    items = [map_item(raw) for raw in raw_items]
    return AsyncPage(
        items=items,
        next_page_token=_next_page_token_from_response(data),
        _fetch_page=fetch_page,
    )


def build_aip_page_raw(
    data: Dict[str, Any],
    items_key: str,
    fetch_page: Callable[[str], Page[Dict[str, Any]]],
) -> Page[Dict[str, Any]]:
    """Construct Page[dict] from an AIP list response (e.g. context item values)."""
    if not isinstance(data, dict) or items_key not in data:
        raise ModusError(
            f"Unexpected list response shape: missing {items_key!r}. "
            f"Got: {type(data).__name__}. This is likely a backend error."
        )
    items: List[Dict[str, Any]] = [dict(x) for x in _require_items_list(data, items_key)]
    return Page(
        items=items,
        next_page_token=_next_page_token_from_response(data),
        _fetch_page=fetch_page,
    )


def build_async_aip_page_raw(
    data: Dict[str, Any],
    items_key: str,
    fetch_page: Callable[[str], Awaitable[AsyncPage[Dict[str, Any]]]],
) -> AsyncPage[Dict[str, Any]]:
    """Construct AsyncPage[dict] from an AIP list response."""
    if not isinstance(data, dict) or items_key not in data:
        raise ModusError(
            f"Unexpected list response shape: missing {items_key!r}. "
            f"Got: {type(data).__name__}. This is likely a backend error."
        )
    items: List[Dict[str, Any]] = [dict(x) for x in _require_items_list(data, items_key)]
    return AsyncPage(
        items=items,
        next_page_token=_next_page_token_from_response(data),
        _fetch_page=fetch_page,
    )
