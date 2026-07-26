"""Search and manage long-term memories for a scope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._pagination import (
    aip_list_params,
    build_aip_page_mapped,
    build_async_aip_page_mapped,
)
from modus._query import update_mask_query
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id, validate_page_size
from modus.types.pagination import AsyncPage, Page

from ...types.memories import Memory, MemorySearchRequest, MemorySearchResult, MemoryUpdate


@dataclass(frozen=True)
class ScopeMemoriesOperations:
    """Which scope memory operationIds this sub-resource calls."""

    list: str
    search: str
    update: str
    delete: str


SCOPE_MEMORY_OPERATIONS = ScopeMemoriesOperations(
    list="ScopeMemoriesController_list",
    search="ScopeMemoriesController_search",
    update="ScopeMemoriesController_update",
    delete="ScopeMemoriesController_delete",
)


def _validate_memory_id(memory_id: str) -> None:
    validate_id(memory_id, name="memory_id")


def _map_memory(raw: dict) -> Memory:
    return Memory.model_validate(raw)


def _map_search_result(raw: dict) -> MemorySearchResult:
    return MemorySearchResult.model_validate(raw)


class ScopeMemoriesResource:
    def __init__(
        self,
        http: HttpClient,
        config: ModusConfig,
        scope_id: Union[int, str],
        ops: ScopeMemoriesOperations = SCOPE_MEMORY_OPERATIONS,
    ) -> None:
        self._http = http
        self._config = config
        self._scope_id = scope_id
        self._ops = ops

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Page[Memory]:
        """
        List memories stored for this scope.

        Args:
            page_size:  Items per page (default 25).
            page_token: Token from a previous page's ``next_page_token``.
            user_id:    Optional end-user scope when memories are scoped per user.
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
                self._ops.list,
                path_params={"id": self._scope_id},
                query=params,
            ),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "memories",
            _map_memory,
            lambda cur: self._list_page(page_size, cur, user_id),
        )

    def search(
        self,
        request: MemorySearchRequest,
    ) -> MemorySearchResult:
        """
        Search this scope's memories by natural-language query.

        Args:
            request: Query text and optional ``user_id`` / ``limit``.
        """
        validate_id(self._scope_id, name="scope_id")
        body = request.model_dump(by_alias=True, exclude_none=True)
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.search,
                path_params={"id": self._scope_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return _map_search_result(raw)

    def update(
        self,
        memory_id: str,
        update: MemoryUpdate,
        *,
        update_mask: Optional[str] = None,
    ) -> Memory:
        """
        Update one memory. Requires manage permission on the scope.

        Args:
            memory_id:   Id from list or search.
            update:      Fields to change (``memory`` and/or ``metadata``).
            update_mask: Optional comma-separated field names to update.
        """
        _validate_memory_id(memory_id)
        validate_id(self._scope_id, name="scope_id")
        body = update.model_dump(by_alias=True, exclude_none=True)
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.update,
                path_params={"id": self._scope_id, "memoryId": memory_id},
                query=update_mask_query(update_mask),
                json_body=body,
            ),
            self._config.max_retries,
        )
        return _map_memory(raw)

    def delete(self, memory_id: str) -> None:
        """Delete one memory (idempotent 204)."""
        _validate_memory_id(memory_id)
        validate_id(self._scope_id, name="scope_id")
        with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.delete,
                path_params={"id": self._scope_id, "memoryId": memory_id},
            ),
            self._config.max_retries,
        )


class AsyncScopeMemoriesResource:
    def __init__(
        self,
        http: AsyncHttpClient,
        config: ModusConfig,
        scope_id: Union[int, str],
        ops: ScopeMemoriesOperations = SCOPE_MEMORY_OPERATIONS,
    ) -> None:
        self._http = http
        self._config = config
        self._scope_id = scope_id
        self._ops = ops

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> AsyncPage[Memory]:
        """List memories stored for this scope. See the sync ``list`` for argument details."""
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
                self._ops.list,
                path_params={"id": self._scope_id},
                query=params,
            ),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "memories",
            _map_memory,
            lambda cur: self._list_page(page_size, cur, user_id),
        )

    async def search(self, request: MemorySearchRequest) -> MemorySearchResult:
        """Search this scope's memories by natural-language query. See the sync ``search`` for argument details."""
        validate_id(self._scope_id, name="scope_id")
        body = request.model_dump(by_alias=True, exclude_none=True)
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.search,
                path_params={"id": self._scope_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return _map_search_result(raw)

    async def update(
        self,
        memory_id: str,
        update: MemoryUpdate,
        *,
        update_mask: Optional[str] = None,
    ) -> Memory:
        """Update one memory. See the sync ``update`` for argument details."""
        _validate_memory_id(memory_id)
        validate_id(self._scope_id, name="scope_id")
        body = update.model_dump(by_alias=True, exclude_none=True)
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.update,
                path_params={"id": self._scope_id, "memoryId": memory_id},
                query=update_mask_query(update_mask),
                json_body=body,
            ),
            self._config.max_retries,
        )
        return _map_memory(raw)

    async def delete(self, memory_id: str) -> None:
        """Delete one memory (idempotent). See the sync ``delete`` for argument details."""
        _validate_memory_id(memory_id)
        validate_id(self._scope_id, name="scope_id")
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.delete,
                path_params={"id": self._scope_id, "memoryId": memory_id},
            ),
            self._config.max_retries,
        )
