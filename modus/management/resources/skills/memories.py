"""Skill memories sub-resource — /api/v1/skills/:id/memories."""

from __future__ import annotations

from typing import Optional, Union
from urllib.parse import quote

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._pagination import (
    aip_list_params,
    build_aip_page_mapped,
    build_async_aip_page_mapped,
)
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id, validate_page_size
from modus.types.pagination import AsyncPage, Page

from ...types.memories import Memory, MemorySearchRequest, MemorySearchResult, MemoryUpdate


def _validate_memory_id(memory_id: str) -> None:
    validate_id(memory_id, name="memory_id")


def _map_memory(raw: dict) -> Memory:
    return Memory.model_validate(raw)


def _map_search_result(raw: dict) -> MemorySearchResult:
    return MemorySearchResult.model_validate(raw)


class MemoriesResource:
    def __init__(
        self,
        http: HttpClient,
        config: ModusConfig,
        skill_id: Union[int, str],
    ) -> None:
        self._http = http
        self._config = config
        self._skill_id = skill_id

    def _base_path(self) -> str:
        validate_id(self._skill_id, name="skill_id")
        safe_id = quote(str(self._skill_id), safe="")
        return f"/api/v1/skills/{safe_id}/memories"

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Page[Memory]:
        """
        List memories stored for this skill.

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
        params = aip_list_params(page_size, page_token)
        if user_id is not None:
            params["userId"] = user_id
        data = with_retry(
            lambda: self._http.get(self._base_path(), params=params),
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
        Search this skill's memories by natural-language query.

        Args:
            request: Query text and optional ``user_id`` / ``limit``.
        """
        body = request.model_dump(by_alias=True, exclude_none=True)
        raw = with_retry(
            lambda: self._http.post(f"{self._base_path()}/search", json=body),
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
        Update one memory. Requires manage permission on the skill.

        Args:
            memory_id:   Id from list or search.
            update:      Fields to change (``memory`` and/or ``metadata``).
            update_mask: Optional comma-separated field names to update.
        """
        _validate_memory_id(memory_id)
        safe_mid = quote(memory_id, safe="")
        url = f"{self._base_path()}/{safe_mid}"
        if update_mask is not None:
            url = f"{url}?updateMask={quote(update_mask, safe='')}"
        body = update.model_dump(by_alias=True, exclude_none=True)
        raw = with_retry(
            lambda: self._http.patch(url, json=body),
            self._config.max_retries,
        )
        return _map_memory(raw)

    def delete(self, memory_id: str) -> None:
        """Delete one memory (idempotent 204)."""
        _validate_memory_id(memory_id)
        safe_mid = quote(memory_id, safe="")
        with_retry(
            lambda: self._http.delete(f"{self._base_path()}/{safe_mid}"),
            self._config.max_retries,
        )


class AsyncMemoriesResource:
    def __init__(
        self,
        http: AsyncHttpClient,
        config: ModusConfig,
        skill_id: Union[int, str],
    ) -> None:
        self._http = http
        self._config = config
        self._skill_id = skill_id

    def _base_path(self) -> str:
        validate_id(self._skill_id, name="skill_id")
        safe_id = quote(str(self._skill_id), safe="")
        return f"/api/v1/skills/{safe_id}/memories"

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> AsyncPage[Memory]:
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token, user_id)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        user_id: Optional[str],
    ) -> AsyncPage[Memory]:
        params = aip_list_params(page_size, page_token)
        if user_id is not None:
            params["userId"] = user_id
        data = await async_with_retry(
            lambda: self._http.get(self._base_path(), params=params),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "memories",
            _map_memory,
            lambda cur: self._list_page(page_size, cur, user_id),
        )

    async def search(self, request: MemorySearchRequest) -> MemorySearchResult:
        body = request.model_dump(by_alias=True, exclude_none=True)
        raw = await async_with_retry(
            lambda: self._http.post(f"{self._base_path()}/search", json=body),
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
        _validate_memory_id(memory_id)
        safe_mid = quote(memory_id, safe="")
        url = f"{self._base_path()}/{safe_mid}"
        if update_mask is not None:
            url = f"{url}?updateMask={quote(update_mask, safe='')}"
        body = update.model_dump(by_alias=True, exclude_none=True)
        raw = await async_with_retry(
            lambda: self._http.patch(url, json=body),
            self._config.max_retries,
        )
        return _map_memory(raw)

    async def delete(self, memory_id: str) -> None:
        _validate_memory_id(memory_id)
        safe_mid = quote(memory_id, safe="")
        await async_with_retry(
            lambda: self._http.delete(f"{self._base_path()}/{safe_mid}"),
            self._config.max_retries,
        )
