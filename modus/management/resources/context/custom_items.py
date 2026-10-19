"""Custom context items resource — customer-owned context CRUD."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from modus._config import ModusConfig
from modus._exceptions import ModusError
from modus._generated.models import BatchCreateCustomContextItemRelationsResponseDto
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
    "from_uid": "fromUid",
    "to_uid": "toUid",
    "relation_type": "relationType",
}


def _omit_none(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _with_created_uid(data: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(data)
    context_item_id = out.get("contextItemId")
    if not isinstance(context_item_id, str) or not context_item_id:
        raise ModusError(
            "Custom context create response missing non-empty string contextItemId"
        )
    out["uid"] = context_item_id
    return out


def _wire_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _omit_none(
        {_FIELD_ALIASES.get(key, key): value for key, value in payload.items()}
    )


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
            search_query: Word search: returns rows that contain every word of
                the query, case-insensitive.
            topics: Optional topic filters.

        Returns:
            A page of custom context items.

        Example:
            >>> for item in mgmt.context.custom_items.list(page_size=25).auto_paging_iter():
            ...     print(item.uid, item.context_type)
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

        Example:
            >>> item = mgmt.context.custom_items.get("PLACEHOLDER_UID")
            >>> item.context_type
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
        """Create a custom context item for an internal system or custom database.

        Args:
            **payload: Item fields such as ``kind``, ``source_id``, ``name``,
                ``content``, and optional hierarchy / attribute keys.

        Returns:
            Create acknowledgement dict including ``uid``.

        Example:
            >>> created = mgmt.context.custom_items.create(
            ...     kind="entity",
            ...     source_id="my-source",
            ...     name="Q3 churn notes",
            ...     content={"summary": "Key findings…"},
            ... )
            >>> created["uid"]
        """
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "CustomContextItemsController_create",
                json_body=_wire_payload(payload),
            ),
            self._config.max_retries,
        )
        return _with_created_uid(dict(data))

    def batch_create(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create or update a batch of custom context items by stable hierarchy.

        Args:
            items: Payloads with the same shape as ``create`` (``kind``,
                ``source_id`` / ``sourceId``, ``name``, ``content``, …).

        Returns:
            List of create acknowledgement dicts, each including ``uid``.

        Example:
            >>> created = mgmt.context.custom_items.batch_create(
            ...     [
            ...         {
            ...             "kind": "entity",
            ...             "sourceId": "my-source",
            ...             "name": "Q3 churn notes",
            ...             "content": {"summary": "Key findings"},
            ...         }
            ...     ]
            ... )
            >>> print(created[0]["uid"])
        """
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "CustomContextItemsController_batchCreate",
                json_body={"items": [_wire_payload(item) for item in items]},
            ),
            self._config.max_retries,
        )
        raw_items = dict(data).get("contextItems", [])
        return (
            [_with_created_uid(dict(item)) for item in raw_items]
            if isinstance(raw_items, list)
            else []
        )

    def create_relations(self, relations: List[Dict[str, Any]]) -> int:
        """Create or update typed relations between context items.

        Args:
            relations: Relations containing ``from_uid``, ``to_uid``,
                ``relation_type``, and optional structured ``content``.

        Returns:
            Number of relations created or updated.

        Example:
            >>> count = mgmt.context.custom_items.create_relations(
            ...     [{
            ...         "from_uid": "SOURCE_UID",
            ...         "to_uid": "TARGET_UID",
            ...         "relation_type": "depends_on",
            ...     }]
            ... )
        """
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "CustomContextItemsController_createRelations",
                json_body={
                    "relations": [_wire_payload(relation) for relation in relations]
                },
            ),
            self._config.max_retries,
        )
        return int(
            BatchCreateCustomContextItemRelationsResponseDto.model_validate(
                data
            ).upserted_count
        )

    def update(self, uid: str, **payload: Any) -> Dict[str, Any]:
        """Update mutable fields on a custom context item.

        Args:
            uid: Custom context item identifier.
            **payload: Fields to update, such as description or topics.

        Returns:
            The update acknowledgement payload.

        Example:
            >>> mgmt.context.custom_items.update(
            ...     "PLACEHOLDER_UID",
            ...     description="Updated summary",
            ... )
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

        Example:
            >>> result = mgmt.context.custom_items.delete("PLACEHOLDER_UID")
            >>> result.uid
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
            search_query: Word search: returns rows that contain every word of
                the query, case-insensitive.
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
        return _with_created_uid(dict(data))

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
        return (
            [_with_created_uid(dict(item)) for item in raw_items]
            if isinstance(raw_items, list)
            else []
        )

    async def create_relations(self, relations: List[Dict[str, Any]]) -> int:
        """Create or update typed relations between context items.

        Args:
            relations: Relations containing ``from_uid``, ``to_uid``,
                ``relation_type``, and optional structured ``content``.

        Returns:
            Number of relations created or updated.
        """
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "CustomContextItemsController_createRelations",
                json_body={
                    "relations": [_wire_payload(relation) for relation in relations]
                },
            ),
            self._config.max_retries,
        )
        return int(
            BatchCreateCustomContextItemRelationsResponseDto.model_validate(
                data
            ).upserted_count
        )

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
