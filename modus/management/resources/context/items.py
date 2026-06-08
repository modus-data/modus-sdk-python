"""Context items resource — full CRUD for modus.management."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import quote

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._pagination import (
    aip_list_params,
    build_aip_page,
    build_async_aip_page,
)
from modus._query import with_update_mask as _with_update_mask
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_page_size
from modus.types.pagination import AsyncPage, Page

from ...types.context import (
    ContextItem,
    ContextItemDeletion,
    ContextItemUpdate,
    UserFeedback,
)


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
        content: Optional[Any] = None,
        context_type: Optional[str] = None,
        description: Optional[str] = None,
        user_feedback: Optional[UserFeedback] = None,
        topics: Optional[List[str]] = None,
        update_mask: Optional[str] = None,
    ) -> ContextItem:
        """Update a context item.

        Args:
            uid:           UUID of the context item to update.
            content:       Replacement type-specific content, if changing it.
            context_type:  The item's type (e.g. ``"note"``). Required when ``content`` is supplied.
            description:   New description, if changing it.
            user_feedback: Feedback verdict — ``"positive"``, ``"neutral"``, or ``"negative"``.
            topics:        Replacement topic tags. Pass ``[]`` to clear all tags.
            update_mask:   Comma-separated field names to clear. Name a field here and
                           leave its argument unset to set it to null on the server;
                           fields not named in the mask are left untouched.

        Only the fields you pass are changed; omitted fields are left as-is.
        """
        payload = ContextItemUpdate(
            content=content,
            context_type=context_type,
            description=description,
            user_feedback=user_feedback,
            topics=topics,
        ).model_dump(by_alias=True, exclude_none=update_mask is None)
        safe_uid = quote(uid, safe="")
        path = _with_update_mask(f"/api/v1/context/items/{safe_uid}", update_mask)
        with_retry(
            lambda: self._http.patch(path, json=payload),
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
        content: Optional[Any] = None,
        context_type: Optional[str] = None,
        description: Optional[str] = None,
        user_feedback: Optional[UserFeedback] = None,
        topics: Optional[List[str]] = None,
        update_mask: Optional[str] = None,
    ) -> ContextItem:
        """Update a context item. See the sync ``update`` for argument details."""
        payload = ContextItemUpdate(
            content=content,
            context_type=context_type,
            description=description,
            user_feedback=user_feedback,
            topics=topics,
        ).model_dump(by_alias=True, exclude_none=update_mask is None)
        safe_uid = quote(uid, safe="")
        path = _with_update_mask(f"/api/v1/context/items/{safe_uid}", update_mask)
        await async_with_retry(
            lambda: self._http.patch(path, json=payload),
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
