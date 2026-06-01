"""Context items resource — full CRUD for modus.management."""

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import quote

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._pagination import (
    aip_list_params,
    build_aip_page,
    build_async_aip_page,
)
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_page_size
from modus.types.pagination import AsyncPage, Page

from ...types.context import ContextItem, ContextItemDeletion, ContextItemUpdate


def _context_list_params(
    page_size: int,
    page_token: Optional[str],
    context_type: Optional[str],
) -> Dict[str, Any]:
    extra: Dict[str, Any] = {}
    if context_type is not None:
        extra["contextTypes"] = [context_type]
    return aip_list_params(page_size, page_token, **extra)


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
        safe_uid = quote(uid, safe="")
        data = with_retry(
            lambda: self._http.get(f"/api/v1/context/items/{safe_uid}"),
            self._config.max_retries,
        )
        return ContextItem.model_validate(data)

    def update(
        self,
        uid: str,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[Any] = None,
        verification_status: Optional[str] = None,
    ) -> ContextItem:
        """Update a context item."""
        payload = ContextItemUpdate(
            title=title,
            description=description,
            content=content,
            verification_status=verification_status,
        ).model_dump(by_alias=True, exclude_none=True)
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

    async def update(
        self,
        uid: str,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[Any] = None,
        verification_status: Optional[str] = None,
    ) -> ContextItem:
        payload = ContextItemUpdate(
            title=title,
            description=description,
            content=content,
            verification_status=verification_status,
        ).model_dump(by_alias=True, exclude_none=True)
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
