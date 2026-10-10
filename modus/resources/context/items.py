"""Read context items from the Modus knowledge base."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from ..._config import ModusConfig
from ..._exceptions import NotFoundError
from ..._generated.models import (
    ContentProjectionDto,
    LookupContextItemDto,
    LookupContextItemResponseDto,
)
from ..._http import AsyncHttpClient, HttpClient
from ..._openapi_invoke import invoke_operation, invoke_operation_async
from ..._pagination import (
    aip_list_params,
    build_aip_page,
    build_aip_page_mapped,
    build_async_aip_page,
    build_async_aip_page_mapped,
)
from ..._retry import async_with_retry, with_retry
from ..._validation import DEFAULT_MAX_PAGE_SIZE, validate_page_size
from ...types.context import ContextItem, ContextItemLookupRow
from ...types.context_values import ContextValueRow
from ...types.json_blob import JsonObjectInput, dump_json_object
from ...types.pagination import AsyncPage, Page


def _map_value_row(raw: dict) -> ContextValueRow:
    return ContextValueRow.model_validate(raw)


def _context_list_params(
    page_size: int,
    page_token: Optional[str],
    context_type: Optional[str],
    parent_uids: Optional[Sequence[str]] = None,
    ancestor_uids: Optional[Sequence[str]] = None,
    connection_ids: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    extra: Dict[str, Any] = {}
    if context_type is not None:
        extra["contextTypes"] = [context_type]
    if parent_uids is not None:
        extra["parentUids"] = list(parent_uids) if len(parent_uids) > 0 else ""
    if ancestor_uids is not None:
        extra["ancestorUids"] = list(ancestor_uids) if len(ancestor_uids) > 0 else ""
    if connection_ids is not None:
        extra["connectionIds"] = list(connection_ids) if len(connection_ids) > 0 else ""
    return aip_list_params(page_size, page_token, **extra)


def _parse_lookup_response(raw: Dict[str, Any]) -> Optional[ContextItemLookupRow]:
    """Map lookup body ``{ \"item\": row | null }`` to LookupContextItemRowDto or None."""
    parsed = LookupContextItemResponseDto.model_validate(raw)
    return parsed.item


class ContextItemsResource:
    """
    Read the org knowledge base (notes, metrics, saved queries, integration items).

    Use ``client.context.items`` after ``modus.Modus()``. Prefer ``list`` /
    ``get`` / ``lookup`` for discovery; use ``list_values`` when a field holds
    a large array inside ``content``.

    Example:
        >>> import modus
        >>> client = modus.Modus()
        >>> for item in client.context.items.list(page_size=25).auto_paging_iter():
        ...     print(item.context_type, modus.context_item_label(item), item.uid)
    """

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        context_type: Optional[str] = None,
        parent_uids: Optional[Sequence[str]] = None,
        ancestor_uids: Optional[Sequence[str]] = None,
        connection_ids: Optional[Sequence[str]] = None,
    ) -> Page[ContextItem]:
        """
        List context items in the knowledge base.

        Args:
            page_size:    Items per page (default 25).
            page_token:   Opaque token from a previous page's ``next_page_token``.
            context_type: Filter by type e.g. ``"note"``, ``"metric"``, ``"saved_query"``.
            parent_uids:  Exact ordered native ancestry chain for direct children.
                          Omit to leave parent unrestricted; pass ``[]`` for the
                          known-empty root. Native UIDs are exact tokens; for a
                          folder's children send ancestry UIDs plus the last
                          ``data_path`` token, not the hashed context-item ``uid``.
            ancestor_uids: Ordered UID ancestry prefix for strict descendants.
                          Omit to leave unrestricted; pass ``[]`` for every item
                          with non-null ancestry.
            connection_ids: Restrict to these connection ids. Omit to leave
                          unfiltered; pass ``[]`` to match none. The Files root
                          is ``connection_ids=["files"]`` with ``parent_uids=[]``.

        Returns:
            ``Page[ContextItem]``. Use ``.auto_paging_iter()`` for all pages.
            Print ``modus.context_item_label(item)`` for a human title.

        Example:
            >>> notes = client.context.items.list(context_type="note", page_size=50)
            >>> for item in notes:
            ...     print(modus.context_item_label(item), item.uid)

            >>> root_folders = client.context.items.list(
            ...     connection_ids=["files"],
            ...     context_type="file_folder_metadata",
            ...     parent_uids=[],
            ... )
            >>> folder = root_folders.items[0]
            >>> native_uid = folder.data_path[-1]
            >>> # Known ancestry only — never treat null/omitted ancestry as a root chain.
            >>> if folder.ancestry is not None:
            ...     files = client.context.items.list(
            ...         connection_ids=["files"],
            ...         context_type="file_upload",
            ...         parent_uids=[*(a.uid for a in folder.ancestry), native_uid],
            ...     )
        """
        validate_page_size(page_size)
        return self._list_page(
            page_size,
            page_token,
            context_type,
            parent_uids,
            ancestor_uids,
            connection_ids,
        )

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        context_type: Optional[str],
        parent_uids: Optional[Sequence[str]] = None,
        ancestor_uids: Optional[Sequence[str]] = None,
        connection_ids: Optional[Sequence[str]] = None,
    ) -> Page[ContextItem]:
        params = _context_list_params(
            page_size,
            page_token,
            context_type,
            parent_uids,
            ancestor_uids,
            connection_ids,
        )
        data = with_retry(
            lambda: invoke_operation(
                self._http, "ContextItemsController_list", query=params
            ),
            self._config.max_retries,
        )
        return build_aip_page(
            data,
            "contextItems",
            ContextItem,
            lambda cur: self._list_page(
                page_size,
                cur,
                context_type,
                parent_uids,
                ancestor_uids,
                connection_ids,
            ),
        )

    def get(self, uid: str) -> ContextItem:
        """
        Retrieve a single context item by its UID.

        Args:
            uid: Stable UUID from ``list`` / ``lookup``.

        Returns:
            Full ``ContextItem`` (``uid``, ``context_type``, ``content``, …).

        Raises:
            NotFoundError: if no item with this UID exists.

        Example:
            >>> item = client.context.items.get(uid)
            >>> print(item.context_type, modus.context_item_label(item))
        """
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "ContextItemsController_get",
                path_params={"uid": uid},
            ),
            self._config.max_retries,
        )
        return ContextItem.model_validate(data)

    def lookup(
        self,
        context_type: str,
        data_path: List[str],
        *,
        content_projection: Optional[JsonObjectInput] = None,
    ) -> Optional[ContextItemLookupRow]:
        """
        Look up a context item by type and data path.

        Args:
            context_type:        The context type to search for (e.g. ``"note"``).
            data_path:           Hierarchical path segments that identify the item.
            content_projection:  Optional projection filter for content fields.

        Returns:
            ContextItemLookupRow if found, ``None`` if not found (404).

        Example:
            >>> found = client.context.items.lookup("note", ["finance", "arr-definition"])
            >>> if found:
            ...     print(found.uid, modus.context_item_label(found))
        """
        projection: ContentProjectionDto | None = None
        if content_projection is not None:
            projection = ContentProjectionDto.model_validate(
                dump_json_object(content_projection)
            )
        body = LookupContextItemDto(
            context_type=context_type,
            data_path=data_path,
            content_projection=projection,
        )
        try:
            raw = with_retry(
                lambda: invoke_operation(
                    self._http,
                    "ContextItemsController_lookup",
                    json_body=body.model_dump(by_alias=True, exclude_none=True),
                ),
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
                               partition-aware reads, e.g. ``"table_column"``).
            content_key_path:  Dot-separated JSON path to the array of values inside
                               ``content``. Example: ``"enumValues"`` or ``"sample.values"``.
            page_size:         Values per page (default 25, max 200).
            page_token:        Opaque token from a previous page's ``next_page_token``.

        Returns:
            Page of value entries (shape varies by context type).

        Example:
            >>> # Replace PLACEHOLDER_UID with a real uid whose content has enumValues.
            >>> page = client.context.items.list_values(
            ...     "PLACEHOLDER_UID",
            ...     "table_column",
            ...     "enumValues",
            ...     page_size=25,
            ... )
            >>> for row in page:
            ...     print(row)
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

        Example:
            >>> # Replace PLACEHOLDER_UID with a real uid that has enumValues in content.
            >>> item = client.context.items.get("PLACEHOLDER_UID")
            >>> for row in client.context.items.list_values_for(item, "enumValues"):
            ...     print(row)
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
        params = aip_list_params(
            page_size,
            page_token,
            contextType=context_type,
            contentKeyPath=content_key_path,
        )
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "ContextItemsController_listValues",
                path_params={"uid": uid},
                query=params,
            ),
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
        parent_uids: Optional[Sequence[str]] = None,
        ancestor_uids: Optional[Sequence[str]] = None,
        connection_ids: Optional[Sequence[str]] = None,
    ) -> AsyncPage[ContextItem]:
        """List context items in the knowledge base. See the sync ``list`` for argument details."""
        validate_page_size(page_size)
        return await self._list_page(
            page_size,
            page_token,
            context_type,
            parent_uids,
            ancestor_uids,
            connection_ids,
        )

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        context_type: Optional[str],
        parent_uids: Optional[Sequence[str]] = None,
        ancestor_uids: Optional[Sequence[str]] = None,
        connection_ids: Optional[Sequence[str]] = None,
    ) -> AsyncPage[ContextItem]:
        params = _context_list_params(
            page_size,
            page_token,
            context_type,
            parent_uids,
            ancestor_uids,
            connection_ids,
        )
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, "ContextItemsController_list", query=params
            ),
            self._config.max_retries,
        )
        return build_async_aip_page(
            data,
            "contextItems",
            ContextItem,
            lambda cur: self._list_page(
                page_size,
                cur,
                context_type,
                parent_uids,
                ancestor_uids,
                connection_ids,
            ),
        )

    async def get(self, uid: str) -> ContextItem:
        """Retrieve a context item by its UID. See the sync ``get`` for argument details."""
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ContextItemsController_get",
                path_params={"uid": uid},
            ),
            self._config.max_retries,
        )
        return ContextItem.model_validate(data)

    async def lookup(
        self,
        context_type: str,
        data_path: List[str],
        *,
        content_projection: Optional[JsonObjectInput] = None,
    ) -> Optional[ContextItemLookupRow]:
        """
        Look up a context item by type and data path.

        Args:
            context_type:        The context type to search for.
            data_path:           The data path to match.
            content_projection:  Optional projection filter for content.

        Returns:
            ContextItemLookupRow if found, None if not found (404).
        """
        projection: ContentProjectionDto | None = None
        if content_projection is not None:
            projection = ContentProjectionDto.model_validate(
                dump_json_object(content_projection)
            )
        body = LookupContextItemDto(
            context_type=context_type,
            data_path=data_path,
            content_projection=projection,
        )
        try:
            raw = await async_with_retry(
                lambda: invoke_operation_async(
                    self._http,
                    "ContextItemsController_lookup",
                    json_body=body.model_dump(by_alias=True, exclude_none=True),
                ),
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
                               partition-aware reads, e.g. "table_column").
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
        params = aip_list_params(
            page_size,
            page_token,
            contextType=context_type,
            contentKeyPath=content_key_path,
        )
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ContextItemsController_listValues",
                path_params={"uid": uid},
                query=params,
            ),
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
