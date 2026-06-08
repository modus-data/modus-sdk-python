"""Context items resource — /api/v1/context/items (read-only, consumption SDK)"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import quote

from ..._config import ModusConfig
from ..._exceptions import NotFoundError
from ..._http import AsyncHttpClient, HttpClient
from ..._pagination import (
    aip_list_params,
    build_aip_page,
    build_aip_page_mapped,
    build_async_aip_page,
    build_async_aip_page_mapped,
)
from ..._retry import async_with_retry, with_retry
from ..._validation import DEFAULT_MAX_PAGE_SIZE, validate_page_size
from ...types.context import ContextItem
from ...types.context_values import ContextValueRow
from ...types.json_blob import JsonObjectInput, dump_json_object
from ...types.pagination import AsyncPage, Page


def _map_value_row(raw: dict) -> ContextValueRow:
    return ContextValueRow.model_validate(raw)


def _context_list_params(
    page_size: int,
    page_token: Optional[str],
    context_type: Optional[str],
) -> Dict[str, Any]:
    extra: Dict[str, Any] = {}
    if context_type is not None:
        extra["contextTypes"] = [context_type]
    return aip_list_params(page_size, page_token, **extra)


def _parse_lookup_response(raw: Dict[str, Any]) -> Optional[ContextItem]:
    """Map AIP lookup body ``{ \"item\": row | null }`` to ContextItem or None."""
    if not isinstance(raw, dict):
        raise ValueError("Unexpected lookup response shape")
    if "item" in raw:
        row = raw.get("item")
        if row is None:
            return None
        return ContextItem.model_validate(row)
    return ContextItem.model_validate(raw)


class ContextItemsResource:
    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        context_type: Optional[str] = None,
    ) -> Page[ContextItem]:
        """
        List context items in the knowledge base.

        Args:
            page_size:    Items per page (default 25).
            page_token:   Opaque token from a previous page's ``next_page_token``.
            context_type: Filter by type e.g. "note", "metric", "saved_query".
        """
        validate_page_size(page_size)
        return self._list_page(page_size, page_token, context_type)

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        context_type: Optional[str],
    ) -> Page[ContextItem]:
        params = _context_list_params(page_size, page_token, context_type)
        data = with_retry(
            lambda: self._http.get("/api/v1/context/items", params=params),
            self._config.max_retries,
        )
        return build_aip_page(
            data,
            "contextItems",
            ContextItem,
            lambda cur: self._list_page(page_size, cur, context_type),
        )

    def get(self, uid: str) -> ContextItem:
        """
        Retrieve a single context item by its UID.

        Raises:
            NotFoundError: if no item with this UID exists.
        """
        safe_uid = quote(uid, safe="")
        data = with_retry(
            lambda: self._http.get(f"/api/v1/context/items/{safe_uid}"),
            self._config.max_retries,
        )
        return ContextItem.model_validate(data)

    def lookup(
        self,
        context_type: str,
        data_path: List[str],
        *,
        content_projection: Optional[JsonObjectInput] = None,
    ) -> Optional[ContextItem]:
        """
        POST /api/v1/context/items/lookup — returns None when no match (404).

        Args:
            context_type:        The context type to search for.
            data_path:           The data path to match.
            content_projection:  Optional projection filter for content.

        Returns:
            ContextItem if found, None if not found (404).
        """
        payload: Dict[str, Any] = {"contextType": context_type, "dataPath": data_path}
        if content_projection is not None:
            payload["contentProjection"] = dump_json_object(content_projection)
        try:
            raw = with_retry(
                lambda: self._http.post("/api/v1/context/items/lookup", json=payload),
                self._config.max_retries,
            )
        except NotFoundError:
            return None
        return _parse_lookup_response(raw)

    def list_values(
        self,
        uid: str,
        context_type: str,
        content_key_path: str,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> Page[ContextValueRow]:
        """
        List paginated values for a specific field within a context item.

        Args:
            uid:               The context item's UUID.
            context_type:      Context type of the item (required by the backend for
                               partition-aware reads, e.g. "salesforce_object_field").
            content_key_path:  Dot-separated JSON path to the array of values inside
                               ``content``. Example: ``"enumValues"`` or ``"sample.values"``.
            page_size:         Values per page (default 25, max 200).
            page_token:        Opaque token from a previous page's ``next_page_token``.

        Returns:
            Page of value entries (shape varies by context type).
        """
        validate_page_size(page_size, max_page_size=DEFAULT_MAX_PAGE_SIZE)
        return self._list_values_page(uid, context_type, content_key_path, page_size, page_token)

    def list_values_for(
        self,
        item: ContextItem,
        content_key_path: str,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> Page[ContextValueRow]:
        """
        List paginated values for a field, reusing a context item you already have.

        Same as ``list_values`` but takes a ``ContextItem`` (from ``list`` or
        ``get``) so you do not have to repeat its ``uid`` and ``context_type``.

        Args:
            item:              A context item returned by ``list`` or ``get``.
            content_key_path:  Dot-separated JSON path to the array of values inside
                               ``content``. Example: ``"enumValues"`` or ``"sample.values"``.
            page_size:         Values per page (default 25, max 200).
            page_token:        Opaque token from a previous page's ``next_page_token``.
        """
        return self.list_values(
            item.uid,
            item.context_type,
            content_key_path,
            page_size=page_size,
            page_token=page_token,
        )

    def _list_values_page(
        self,
        uid: str,
        context_type: str,
        content_key_path: str,
        page_size: int,
        page_token: Optional[str],
    ) -> Page[ContextValueRow]:
        safe_uid = quote(uid, safe="")
        params = aip_list_params(
            page_size,
            page_token,
            contextType=context_type,
            contentKeyPath=content_key_path,
        )
        data = with_retry(
            lambda: self._http.get(f"/api/v1/context/items/{safe_uid}/values", params=params),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "values",
            _map_value_row,
            lambda cur: self._list_values_page(
                uid, context_type, content_key_path, page_size, cur
            ),
        )


class AsyncContextItemsResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        context_type: Optional[str] = None,
    ) -> AsyncPage[ContextItem]:
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token, context_type)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        context_type: Optional[str],
    ) -> AsyncPage[ContextItem]:
        params = _context_list_params(page_size, page_token, context_type)
        data = await async_with_retry(
            lambda: self._http.get("/api/v1/context/items", params=params),
            self._config.max_retries,
        )
        return build_async_aip_page(
            data,
            "contextItems",
            ContextItem,
            lambda cur: self._list_page(page_size, cur, context_type),
        )

    async def get(self, uid: str) -> ContextItem:
        safe_uid = quote(uid, safe="")
        data = await async_with_retry(
            lambda: self._http.get(f"/api/v1/context/items/{safe_uid}"),
            self._config.max_retries,
        )
        return ContextItem.model_validate(data)

    async def lookup(
        self,
        context_type: str,
        data_path: List[str],
        *,
        content_projection: Optional[JsonObjectInput] = None,
    ) -> Optional[ContextItem]:
        """
        POST /api/v1/context/items/lookup — returns None when no match (404).

        Args:
            context_type:        The context type to search for.
            data_path:           The data path to match.
            content_projection:  Optional projection filter for content.

        Returns:
            ContextItem if found, None if not found (404).
        """
        payload: Dict[str, Any] = {"contextType": context_type, "dataPath": data_path}
        if content_projection is not None:
            payload["contentProjection"] = dump_json_object(content_projection)
        try:
            raw = await async_with_retry(
                lambda: self._http.post("/api/v1/context/items/lookup", json=payload),
                self._config.max_retries,
            )
        except NotFoundError:
            return None
        return _parse_lookup_response(raw)

    async def list_values(
        self,
        uid: str,
        context_type: str,
        content_key_path: str,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> AsyncPage[ContextValueRow]:
        """
        List paginated values for a specific field within a context item.

        Args:
            uid:               The context item's UUID.
            context_type:      Context type of the item (required by the backend for
                               partition-aware reads, e.g. "salesforce_object_field").
            content_key_path:  Dot-separated JSON path to the array of values inside
                               ``content``. Example: ``"enumValues"`` or ``"sample.values"``.
            page_size:         Values per page (default 25, max 200).
            page_token:        Opaque token from a previous page's ``next_page_token``.

        Returns:
            AsyncPage of value entries (shape varies by context type).
        """
        validate_page_size(page_size, max_page_size=DEFAULT_MAX_PAGE_SIZE)
        return await self._list_values_page(
            uid, context_type, content_key_path, page_size, page_token
        )

    async def list_values_for(
        self,
        item: ContextItem,
        content_key_path: str,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> AsyncPage[ContextValueRow]:
        """
        List paginated values for a field, reusing a context item you already have.

        Same as ``list_values`` but takes a ``ContextItem`` (from ``list`` or
        ``get``) so you do not have to repeat its ``uid`` and ``context_type``.
        """
        return await self.list_values(
            item.uid,
            item.context_type,
            content_key_path,
            page_size=page_size,
            page_token=page_token,
        )

    async def _list_values_page(
        self,
        uid: str,
        context_type: str,
        content_key_path: str,
        page_size: int,
        page_token: Optional[str],
    ) -> AsyncPage[ContextValueRow]:
        safe_uid = quote(uid, safe="")
        params = aip_list_params(
            page_size,
            page_token,
            contextType=context_type,
            contentKeyPath=content_key_path,
        )
        data = await async_with_retry(
            lambda: self._http.get(f"/api/v1/context/items/{safe_uid}/values", params=params),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "values",
            _map_value_row,
            lambda cur: self._list_values_page(
                uid, context_type, content_key_path, page_size, cur
            ),
        )
