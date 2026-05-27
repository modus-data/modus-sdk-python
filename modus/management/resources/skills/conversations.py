"""Skill conversations resource — identical to consumption SDK."""
from __future__ import annotations
from typing import Union
from urllib.parse import quote

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._retry import async_with_retry, with_retry
from ...types.conversations import Conversation, ConversationListItem
from modus.types.pagination import AsyncPage, Page


def _validate_page_params(page: int, page_size: int) -> None:
    if page < 1:
        raise ValueError("page must be >= 1")
    if page_size < 1:
        raise ValueError("page_size must be >= 1")


class ConversationsResource:
    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(self, skill_id: Union[int, str], *, page: int = 1,
             page_size: int = 20) -> Page[ConversationListItem]:
        return self._list_page(skill_id, page, page_size)

    def _list_page(self, skill_id: Union[int, str], page: int,
                   page_size: int) -> Page[ConversationListItem]:
        _validate_page_params(page, page_size)
        params = {"page": page - 1, "pageSize": page_size}
        safe_id = quote(str(skill_id), safe="")
        data = with_retry(
            lambda: self._http.get(f"/api/v1/skills/{safe_id}/conversations", params=params),
            self._config.max_retries,
        )
        items = [ConversationListItem.model_validate(r) for r in data.get("items", [])]
        total_count = data.get("totalCount", 0)
        has_more = page * page_size < total_count
        next_cursor = str(page + 1) if has_more else None
        return Page(
            items=items,
            next_cursor=next_cursor,
            _fetch_page=lambda cur: self._list_page(skill_id, int(cur), page_size),
        )

    def get(self, skill_id: Union[int, str], thread_id: str) -> Conversation:
        safe_id = quote(str(skill_id), safe="")
        safe_tid = quote(str(thread_id), safe="")
        data = with_retry(
            lambda: self._http.get(f"/api/v1/skills/{safe_id}/conversations/{safe_tid}"),
            self._config.max_retries,
        )
        return Conversation.model_validate(data)


class AsyncConversationsResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list(self, skill_id: Union[int, str], *, page: int = 1,
                   page_size: int = 20) -> AsyncPage[ConversationListItem]:
        return await self._list_page(skill_id, page, page_size)

    async def _list_page(self, skill_id: Union[int, str], page: int,
                         page_size: int) -> AsyncPage[ConversationListItem]:
        _validate_page_params(page, page_size)
        params = {"page": page - 1, "pageSize": page_size}
        safe_id = quote(str(skill_id), safe="")
        data = await async_with_retry(
            lambda: self._http.get(f"/api/v1/skills/{safe_id}/conversations", params=params),
            self._config.max_retries,
        )
        items = [ConversationListItem.model_validate(r) for r in data.get("items", [])]
        total_count = data.get("totalCount", 0)
        has_more = page * page_size < total_count
        next_cursor = str(page + 1) if has_more else None
        return AsyncPage(
            items=items,
            next_cursor=next_cursor,
            _fetch_page=lambda cur: self._list_page(skill_id, int(cur), page_size),
        )

    async def get(self, skill_id: Union[int, str], thread_id: str) -> Conversation:
        safe_id = quote(str(skill_id), safe="")
        safe_tid = quote(str(thread_id), safe="")
        data = await async_with_retry(
            lambda: self._http.get(f"/api/v1/skills/{safe_id}/conversations/{safe_tid}"),
            self._config.max_retries,
        )
        return Conversation.model_validate(data)
