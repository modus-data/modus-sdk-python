"""Custom context items resource — customer-owned context CRUD."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._pagination import (
    aip_list_params,
    build_aip_page,
    build_async_aip_page,
)
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_page_size
from modus.types.pagination import AsyncPage, Page

from ...types.context import ContextItem, ContextItemDeletion

_FIELD_ALIASES = {
    "source_id": "sourceId",
    "source_name": "sourceName",
    "collection_id": "collectionId",
    "collection_name": "collectionName",
    "external_id": "externalId",
    "field_name": "fieldName",
    "entity_type": "entityType",
    "data_type": "dataType",
    "idempotency_key": "idempotencyKey",
}


def _omit_none(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _wire_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _omit_none({_FIELD_ALIASES.get(key, key): value for key, value in payload.items()})


def _custom_list_params(
    page_size: int,
    page_token: Optional[str],
    search_query: Optional[str],
    topics: Optional[List[str]],
) -> Dict[str, Any]:
    return aip_list_params(
        page_size,
        page_token,
        **_omit_none({"searchQuery": search_query, "topics": topics}),
    )


class CustomContextItemsResource:
    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        search_query: Optional[str] = None,
        topics: Optional[List[str]] = None,
    ) -> Page[ContextItem]:
        """List custom context items in the organization.

        Args:
            page_size: Maximum items per page.
            page_token: Cursor from a previous page.
            search_query: Optional free-text filter.
            topics: Optional topic filters.

        Returns:
            A page of custom context items.
        """
        validate_page_size(page_size)
        return self._list_page(page_size, page_token, search_query, topics)

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        search_query: Optional[str],
        topics: Optional[List[str]],
    ) -> Page[ContextItem]:
        params = _custom_list_params(page_size, page_token, search_query, topics)
        data = with_retry(
            lambda: invoke_operation(
                self._http, "CustomContextItemsController_list", query=params
            ),
            self._config.max_retries,
        )
        return build_aip_page(
            data,
            "contextItems",
            ContextItem,
            lambda cur: self._list_page(page_size, cur, search_query, topics),
        )

    def get(self, uid: str) -> ContextItem:
        """Fetch one custom context item by uid.

        Args:
            uid: Custom context item identifier.

        Returns:
            The matching custom context item.
        """
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "CustomContextItemsController_get",
                path_params={"uid": uid},
            ),
            self._config.max_retries,
        )
        return ContextItem.model_validate(data)

    def create(self, **payload: Any) -> Dict[str, Any]:
        """Create a custom context item for an internal system or custom database."""
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "CustomContextItemsController_create",
                json_body=_wire_payload(payload),
            ),
            self._config.max_retries,
        )
        return dict(data)

    def batch_create(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create or update a batch of custom context items by stable hierarchy."""
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "CustomContextItemsController_batchCreate",
                json_body={"items": [_wire_payload(item) for item in items]},
            ),
            self._config.max_retries,
        )
        raw_items = dict(data).get("contextItems", [])
        return [dict(item) for item in raw_items] if isinstance(raw_items, list) else []

    def update(self, uid: str, **payload: Any) -> Dict[str, Any]:
        """Update mutable fields on a custom context item.

        Args:
            uid: Custom context item identifier.
            **payload: Fields to update, such as description or topics.

        Returns:
            The update acknowledgement payload.
        """
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "CustomContextItemsController_update",
                path_params={"uid": uid},
                json_body=_wire_payload(payload),
            ),
            self._config.max_retries,
        )
        return dict(data)

    def delete(self, uid: str) -> ContextItemDeletion:
        """Delete a custom context item.

        Args:
            uid: Custom context item identifier.

        Returns:
            Deletion metadata for the removed item.
        """
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "CustomContextItemsController_delete",
                path_params={"uid": uid},
            ),
            self._config.max_retries,
        )
        return ContextItemDeletion.model_validate(raw)


class AsyncCustomContextItemsResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        search_query: Optional[str] = None,
        topics: Optional[List[str]] = None,
    ) -> AsyncPage[ContextItem]:
        """List custom context items in the organization.

        Args:
            page_size: Maximum items per page.
            page_token: Cursor from a previous page.
            search_query: Optional free-text filter.
            topics: Optional topic filters.

        Returns:
            A page of custom context items.
        """
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token, search_query, topics)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        search_query: Optional[str],
        topics: Optional[List[str]],
    ) -> AsyncPage[ContextItem]:
        params = _custom_list_params(page_size, page_token, search_query, topics)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, "CustomContextItemsController_list", query=params
            ),
            self._config.max_retries,
        )
        return build_async_aip_page(
            data,
            "contextItems",
            ContextItem,
            lambda cur: self._list_page(page_size, cur, search_query, topics),
        )

    async def get(self, uid: str) -> ContextItem:
        """Fetch one custom context item by uid.

        Args:
            uid: Custom context item identifier.

        Returns:
            The matching custom context item.
        """
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "CustomContextItemsController_get",
                path_params={"uid": uid},
            ),
            self._config.max_retries,
        )
        return ContextItem.model_validate(data)

    async def create(self, **payload: Any) -> Dict[str, Any]:
        """Create a custom context item for an internal system or custom database."""
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "CustomContextItemsController_create",
                json_body=_wire_payload(payload),
            ),
            self._config.max_retries,
        )
        return dict(data)

    async def batch_create(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create or update a batch of custom context items by stable hierarchy."""
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "CustomContextItemsController_batchCreate",
                json_body={"items": [_wire_payload(item) for item in items]},
            ),
            self._config.max_retries,
        )
        raw_items = dict(data).get("contextItems", [])
        return [dict(item) for item in raw_items] if isinstance(raw_items, list) else []

    async def update(self, uid: str, **payload: Any) -> Dict[str, Any]:
        """Update mutable fields on a custom context item.

        Args:
            uid: Custom context item identifier.
            **payload: Fields to update, such as description or topics.

        Returns:
            The update acknowledgement payload.
        """
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "CustomContextItemsController_update",
                path_params={"uid": uid},
                json_body=_wire_payload(payload),
            ),
            self._config.max_retries,
        )
        return dict(data)

    async def delete(self, uid: str) -> ContextItemDeletion:
        """Delete a custom context item.

        Args:
            uid: Custom context item identifier.

        Returns:
            Deletion metadata for the removed item.
        """
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "CustomContextItemsController_delete",
                path_params={"uid": uid},
            ),
            self._config.max_retries,
        )
        return ContextItemDeletion.model_validate(raw)
