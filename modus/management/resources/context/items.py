"""Context items resource — full CRUD for modus.management."""

from __future__ import annotations
from typing import Any, Dict, Optional
from urllib.parse import quote

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._pagination import build_async_page, build_page
from modus._retry import async_with_retry, with_retry
from ...types.context import ContextItem, ContextItemDeletion, ContextItemUpdate
from modus.types.pagination import AsyncPage, Page


class ContextItemsResource:
    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(self, *, limit: int = 20, cursor: Optional[str] = None,
             context_type: Optional[str] = None) -> Page[ContextItem]:
        return self._list_page(limit, cursor, context_type)

    def _list_page(self, limit: int, cursor: Optional[str],
                   context_type: Optional[str]) -> Page[ContextItem]:
        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if context_type:
            params["contextType"] = context_type
        data = with_retry(
            lambda: self._http.get("/api/v1/context/items", params=params),
            self._config.max_retries,
        )
        return build_page(data, ContextItem,
                          lambda cur: self._list_page(limit, cur, context_type))

    def get(self, uid: str) -> ContextItem:
        safe_uid = quote(uid, safe="")
        data = with_retry(
            lambda: self._http.get(f"/api/v1/context/items/{safe_uid}"),
            self._config.max_retries,
        )
        return ContextItem.model_validate(data)

    def update(self, uid: str, **kwargs: Any) -> ContextItem:
        """Update a context item. kwargs: title, description, content, verification_status."""
        payload = ContextItemUpdate(**kwargs).model_dump(by_alias=True, exclude_none=True)
        safe_uid = quote(uid, safe="")
        with_retry(
            lambda: self._http.patch(f"/api/v1/context/items/{safe_uid}", json=payload),
            self._config.max_retries,
        )
        return self.get(uid)

    def delete(self, uid: str) -> ContextItemDeletion:
        safe_uid = quote(uid, safe="")
        raw = with_retry(
            lambda: self._http.delete(f"/api/v1/context/items/{safe_uid}"),
            self._config.max_retries,
        )
        return ContextItemDeletion.model_validate(raw)


class AsyncContextItemsResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list(self, *, limit: int = 20, cursor: Optional[str] = None,
                   context_type: Optional[str] = None) -> AsyncPage[ContextItem]:
        return await self._list_page(limit, cursor, context_type)

    async def _list_page(self, limit: int, cursor: Optional[str],
                         context_type: Optional[str]) -> AsyncPage[ContextItem]:
        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if context_type:
            params["contextType"] = context_type
        data = await async_with_retry(
            lambda: self._http.get("/api/v1/context/items", params=params),
            self._config.max_retries,
        )
        return build_async_page(data, ContextItem,
                                lambda cur: self._list_page(limit, cur, context_type))

    async def get(self, uid: str) -> ContextItem:
        safe_uid = quote(uid, safe="")
        data = await async_with_retry(
            lambda: self._http.get(f"/api/v1/context/items/{safe_uid}"),
            self._config.max_retries,
        )
        return ContextItem.model_validate(data)

    async def update(self, uid: str, **kwargs: Any) -> ContextItem:
        payload = ContextItemUpdate(**kwargs).model_dump(by_alias=True, exclude_none=True)
        safe_uid = quote(uid, safe="")
        await async_with_retry(
            lambda: self._http.patch(f"/api/v1/context/items/{safe_uid}", json=payload),
            self._config.max_retries,
        )
        return await self.get(uid)

    async def delete(self, uid: str) -> ContextItemDeletion:
        safe_uid = quote(uid, safe="")
        raw = await async_with_retry(
            lambda: self._http.delete(f"/api/v1/context/items/{safe_uid}"),
            self._config.max_retries,
        )
        return ContextItemDeletion.model_validate(raw)
