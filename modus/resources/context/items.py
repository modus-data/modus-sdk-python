"""Context items resource — /api/v1/context/items (read-only, consumption SDK)"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from ..._config import ModusConfig
from ..._exceptions import NotFoundError
from ..._http import AsyncHttpClient, HttpClient
from ..._pagination import build_async_page, build_page
from ..._retry import async_with_retry, with_retry
from ...types.context import ContextItem
from ...types.pagination import AsyncPage, Page


class ContextItemsResource:
    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(
        self,
        *,
        limit: int = 20,
        cursor: Optional[str] = None,
        context_type: Optional[str] = None,
    ) -> Page[ContextItem]:
        """
        List context items in the knowledge base.

        Args:
            limit:        Items per page (default 20).
            cursor:       Pagination cursor.
            context_type: Filter by type e.g. "note", "metric", "saved_query".
        """
        return self._list_page(limit, cursor, context_type)

    def _list_page(
        self,
        limit: int,
        cursor: Optional[str],
        context_type: Optional[str],
    ) -> Page[ContextItem]:
        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if context_type:
            params["contextType"] = context_type
        data = with_retry(
            lambda: self._http.get("/api/v1/context/items", params=params),
            self._config.max_retries,
        )
        return build_page(
            data,
            ContextItem,
            lambda cur: self._list_page(limit, cur, context_type),
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
        content_projection: Optional[Dict[str, Any]] = None,
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
            payload["contentProjection"] = content_projection
        try:
            raw = with_retry(
                lambda: self._http.post("/api/v1/context/items/lookup", json=payload),
                self._config.max_retries,
            )
        except NotFoundError:
            return None
        return ContextItem.model_validate(raw)

    def list_values(
        self,
        uid: str,
        context_type: str,
        content_key_path: str,
        *,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> Page[Dict[str, Any]]:
        """
        List paginated values for a specific field within a context item.

        Args:
            uid:               The context item's UUID.
            context_type:      Context type of the item (required by the backend for
                               partition-aware reads, e.g. "salesforce_object_field").
            content_key_path:  Dot-separated JSON path to the array of values inside
                               ``content``. Example: ``"enumValues"`` or ``"sample.values"``.
            limit:             Items per page (default 20, max 200).
            cursor:            Pagination cursor from a previous page's next_cursor.

        Returns:
            Page[Dict[str, Any]] of value entries.
        """
        return self._list_values_page(uid, context_type, content_key_path, limit, cursor)

    def _list_values_page(
        self,
        uid: str,
        context_type: str,
        content_key_path: str,
        limit: int,
        cursor: Optional[str],
    ) -> Page[Dict[str, Any]]:
        safe_uid = quote(uid, safe="")
        params: Dict[str, Any] = {
            "contextType": context_type,
            "contentKeyPath": content_key_path,
            "limit": limit,
        }
        if cursor:
            params["cursor"] = cursor
        data = with_retry(
            lambda: self._http.get(f"/api/v1/context/items/{safe_uid}/values", params=params),
            self._config.max_retries,
        )
        if not isinstance(data, dict) or "items" not in data:
            raise ValueError("Unexpected response shape from /values: missing 'items'")
        raw_items = data.get("items", [])
        next_cursor = data.get("nextCursor") or None
        return Page(
            items=raw_items,
            next_cursor=next_cursor,
            _fetch_page=lambda cur: self._list_values_page(uid, context_type, content_key_path, limit, cur),
        )


class AsyncContextItemsResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list(
        self,
        *,
        limit: int = 20,
        cursor: Optional[str] = None,
        context_type: Optional[str] = None,
    ) -> AsyncPage[ContextItem]:
        return await self._list_page(limit, cursor, context_type)

    async def _list_page(
        self,
        limit: int,
        cursor: Optional[str],
        context_type: Optional[str],
    ) -> AsyncPage[ContextItem]:
        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if context_type:
            params["contextType"] = context_type
        data = await async_with_retry(
            lambda: self._http.get("/api/v1/context/items", params=params),
            self._config.max_retries,
        )
        return build_async_page(
            data,
            ContextItem,
            lambda cur: self._list_page(limit, cur, context_type),
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
        content_projection: Optional[Dict[str, Any]] = None,
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
            payload["contentProjection"] = content_projection
        try:
            raw = await async_with_retry(
                lambda: self._http.post("/api/v1/context/items/lookup", json=payload),
                self._config.max_retries,
            )
        except NotFoundError:
            return None
        return ContextItem.model_validate(raw)

    async def list_values(
        self,
        uid: str,
        context_type: str,
        content_key_path: str,
        *,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> AsyncPage[Dict[str, Any]]:
        """
        List paginated values for a specific field within a context item.

        Args:
            uid:               The context item's UUID.
            context_type:      Context type of the item (required by the backend for
                               partition-aware reads, e.g. "salesforce_object_field").
            content_key_path:  Dot-separated JSON path to the array of values inside
                               ``content``. Example: ``"enumValues"`` or ``"sample.values"``.
            limit:             Items per page (default 20, max 200).
            cursor:            Pagination cursor from a previous page's next_cursor.

        Returns:
            AsyncPage[Dict[str, Any]] of value entries.
        """
        return await self._list_values_page(uid, context_type, content_key_path, limit, cursor)

    async def _list_values_page(
        self,
        uid: str,
        context_type: str,
        content_key_path: str,
        limit: int,
        cursor: Optional[str],
    ) -> AsyncPage[Dict[str, Any]]:
        safe_uid = quote(uid, safe="")
        params: Dict[str, Any] = {
            "contextType": context_type,
            "contentKeyPath": content_key_path,
            "limit": limit,
        }
        if cursor:
            params["cursor"] = cursor
        data = await async_with_retry(
            lambda: self._http.get(f"/api/v1/context/items/{safe_uid}/values", params=params),
            self._config.max_retries,
        )
        if not isinstance(data, dict) or "items" not in data:
            raise ValueError("Unexpected response shape from /values: missing 'items'")
        raw_items = data.get("items", [])
        next_cursor = data.get("nextCursor") or None
        return AsyncPage(
            items=raw_items,
            next_cursor=next_cursor,
            _fetch_page=lambda cur: self._list_values_page(uid, context_type, content_key_path, limit, cur),
        )
