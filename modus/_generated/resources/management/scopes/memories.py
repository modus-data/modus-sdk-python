# Auto-generated from the Modus API schema. Do not edit by hand.

from __future__ import annotations

from typing import Optional, Union

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._pagination import aip_list_params, build_aip_page_mapped, build_async_aip_page_mapped
from modus._query import update_mask_query
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id, validate_page_size
from modus.management.types.memories import (
    Memory,
    MemorySearchRequest,
    MemorySearchResult,
    MemoryUpdate,
)
from modus.types.pagination import AsyncPage, Page


class _ScopesMemoriesResourceBase:
    """Generated base for the management ``scopes.memories`` resource."""

    def __init__(self, http: HttpClient, config: ModusConfig, scope_id: Union[int, str]) -> None:
        self._http = http
        self._config = config
        self._scope_id = scope_id

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Page[Memory]:
        """
        List scope memories.

        Returns a page of the scope’s memories (up to 1000 total). Pass ``next_page_token`` as
        ``page_token`` to fetch the next page. Optional ``user_id`` filters to one end user.

        **Requires:** ``scopes:read``

        Args:
            page_size: Items per page. Defaults to 100 when no pagination params are sent (legacy);
                otherwise 25, clamped to 100.
            page_token: Opaque page token from a previous response's ``next_page_token``. Omit for
                the first page.
            user_id: Narrow results to memories tagged with this end-user id.

        Returns:
            A page of memories.
        """
        validate_page_size(page_size)
        return self._list_page(page_size, page_token, user_id)

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        user_id: Optional[str],
    ) -> Page[Memory]:
        validate_id(self._scope_id, name="scope_id")
        params = aip_list_params(page_size, page_token)
        if user_id is not None:
            params["userId"] = user_id
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopeMemoriesController_list",
                path_params={"id": self._scope_id},
                query=params,
            ),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "memories",
            Memory.model_validate,
            lambda cur: self._list_page(page_size, cur, user_id),
        )

    def search(self, request: MemorySearchRequest) -> MemorySearchResult:
        """
        Search scope memories.

        Returns memories ranked by semantic similarity to the supplied ``query``. Caller must at
        least ``use`` the scope. Optional ``user_id`` and ``limit`` body fields narrow the result
        set (legacy parity with ``search-memories``).

        **Requires:** ``scopes:read``

        Args:
            request: Request body; see :class:`MemorySearchRequest`.
        """
        validate_id(self._scope_id, name="scope_id")
        body = request.model_dump(by_alias=True, exclude_none=True)
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopeMemoriesController_search",
                path_params={"id": self._scope_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return MemorySearchResult.model_validate(raw)

    def update(
        self,
        memory_id: str,
        update: MemoryUpdate,
        *,
        update_mask: Optional[str] = None,
    ) -> Memory:
        """
        Update a memory.

        Updates one memory. Supply at least one of ``memory`` or ``metadata``. Use ``update_mask``
        to limit which fields change.

        **Requires:** ``scopes:write``

        Args:
            memory_id: Opaque memory id as returned by the list / search endpoints.
            update: Request body; see :class:`MemoryUpdate`.
            update_mask: Comma-separated list of fields to update. Omit to update all provided
                fields.
        """
        validate_id(memory_id, name="memory_id")
        validate_id(self._scope_id, name="scope_id")
        body = update.model_dump(by_alias=True, exclude_none=True)
        query: dict = {}
        update_mask_params = update_mask_query(update_mask)
        if update_mask_params is not None:
            query.update(update_mask_params)
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopeMemoriesController_update",
                path_params={"id": self._scope_id, "memoryId": memory_id},
                query=query,
                json_body=body,
            ),
            self._config.max_retries,
        )
        return Memory.model_validate(raw)

    def delete(self, memory_id: str) -> None:
        """
        Delete a memory.

        Deletes one memory. Deleting an already-deleted memory is a no-op.

        **Requires:** ``scopes:write``

        Args:
            memory_id: Opaque memory id as returned by the list / search endpoints.
        """
        validate_id(memory_id, name="memory_id")
        validate_id(self._scope_id, name="scope_id")
        with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopeMemoriesController_delete",
                path_params={"id": self._scope_id, "memoryId": memory_id},
            ),
            self._config.max_retries,
        )


class _AsyncScopesMemoriesResourceBase:
    """Generated base for the management ``scopes.memories`` resource."""

    def __init__(
        self,
        http: AsyncHttpClient,
        config: ModusConfig,
        scope_id: Union[int, str],
    ) -> None:
        self._http = http
        self._config = config
        self._scope_id = scope_id

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> AsyncPage[Memory]:
        """
        List scope memories.

        Returns a page of the scope’s memories (up to 1000 total). Pass ``next_page_token`` as
        ``page_token`` to fetch the next page. Optional ``user_id`` filters to one end user.

        **Requires:** ``scopes:read``

        Args:
            page_size: Items per page. Defaults to 100 when no pagination params are sent (legacy);
                otherwise 25, clamped to 100.
            page_token: Opaque page token from a previous response's ``next_page_token``. Omit for
                the first page.
            user_id: Narrow results to memories tagged with this end-user id.

        Returns:
            A page of memories.
        """
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token, user_id)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        user_id: Optional[str],
    ) -> AsyncPage[Memory]:
        validate_id(self._scope_id, name="scope_id")
        params = aip_list_params(page_size, page_token)
        if user_id is not None:
            params["userId"] = user_id
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopeMemoriesController_list",
                path_params={"id": self._scope_id},
                query=params,
            ),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "memories",
            Memory.model_validate,
            lambda cur: self._list_page(page_size, cur, user_id),
        )

    async def search(self, request: MemorySearchRequest) -> MemorySearchResult:
        """
        Search scope memories.

        Returns memories ranked by semantic similarity to the supplied ``query``. Caller must at
        least ``use`` the scope. Optional ``user_id`` and ``limit`` body fields narrow the result
        set (legacy parity with ``search-memories``).

        **Requires:** ``scopes:read``

        Args:
            request: Request body; see :class:`MemorySearchRequest`.
        """
        validate_id(self._scope_id, name="scope_id")
        body = request.model_dump(by_alias=True, exclude_none=True)
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopeMemoriesController_search",
                path_params={"id": self._scope_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return MemorySearchResult.model_validate(raw)

    async def update(
        self,
        memory_id: str,
        update: MemoryUpdate,
        *,
        update_mask: Optional[str] = None,
    ) -> Memory:
        """
        Update a memory.

        Updates one memory. Supply at least one of ``memory`` or ``metadata``. Use ``update_mask``
        to limit which fields change.

        **Requires:** ``scopes:write``

        Args:
            memory_id: Opaque memory id as returned by the list / search endpoints.
            update: Request body; see :class:`MemoryUpdate`.
            update_mask: Comma-separated list of fields to update. Omit to update all provided
                fields.
        """
        validate_id(memory_id, name="memory_id")
        validate_id(self._scope_id, name="scope_id")
        body = update.model_dump(by_alias=True, exclude_none=True)
        query: dict = {}
        update_mask_params = update_mask_query(update_mask)
        if update_mask_params is not None:
            query.update(update_mask_params)
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopeMemoriesController_update",
                path_params={"id": self._scope_id, "memoryId": memory_id},
                query=query,
                json_body=body,
            ),
            self._config.max_retries,
        )
        return Memory.model_validate(raw)

    async def delete(self, memory_id: str) -> None:
        """
        Delete a memory.

        Deletes one memory. Deleting an already-deleted memory is a no-op.

        **Requires:** ``scopes:write``

        Args:
            memory_id: Opaque memory id as returned by the list / search endpoints.
        """
        validate_id(memory_id, name="memory_id")
        validate_id(self._scope_id, name="scope_id")
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopeMemoriesController_delete",
                path_params={"id": self._scope_id, "memoryId": memory_id},
            ),
            self._config.max_retries,
        )
