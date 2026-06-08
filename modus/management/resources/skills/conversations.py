"""Modus skill conversations — /api/v1/skills/:id/conversations (management SDK)"""
from __future__ import annotations

from typing import Optional, Union
from urllib.parse import quote

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._pagination import (
    aip_list_params,
    build_aip_page,
    build_async_aip_page,
)
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id, validate_page_size
from modus.types.pagination import AsyncPage, Page

from ...types.conversations import Conversation, ConversationListItem


class ConversationsResource:
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
        return f"/api/v1/skills/{safe_id}/conversations"

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> Page[ConversationListItem]:
        """
        List conversation threads for this skill, newest first.

        Args:
            page_size:  Maximum number of items to return (default 25).
            page_token: Token from a previous page's ``next_page_token``; omit for the first page.
        """
        validate_page_size(page_size)
        return self._list_page(page_size, page_token)

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
    ) -> Page[ConversationListItem]:
        params = aip_list_params(page_size, page_token)
        data = with_retry(
            lambda: self._http.get(self._base_path(), params=params),
            self._config.max_retries,
        )
        return build_aip_page(
            data,
            "conversations",
            ConversationListItem,
            lambda cur: self._list_page(page_size, cur),
        )

    def get(self, thread_id: str) -> Conversation:
        """
        Retrieve a conversation thread with its full message history.

        Args:
            thread_id: Conversation thread ID.
        """
        validate_id(thread_id, name="thread_id")
        safe_tid = quote(str(thread_id), safe="")
        data = with_retry(
            lambda: self._http.get(f"{self._base_path()}/{safe_tid}"),
            self._config.max_retries,
        )
        return Conversation.model_validate(data)


class AsyncConversationsResource:
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
        return f"/api/v1/skills/{safe_id}/conversations"

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> AsyncPage[ConversationListItem]:
        """
        List conversation threads for this skill, newest first.

        Args:
            page_size:  Maximum number of items to return (default 25).
            page_token: Token from a previous page's ``next_page_token``; omit for the first page.
        """
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
    ) -> AsyncPage[ConversationListItem]:
        params = aip_list_params(page_size, page_token)
        data = await async_with_retry(
            lambda: self._http.get(self._base_path(), params=params),
            self._config.max_retries,
        )
        return build_async_aip_page(
            data,
            "conversations",
            ConversationListItem,
            lambda cur: self._list_page(page_size, cur),
        )

    async def get(self, thread_id: str) -> Conversation:
        """
        Retrieve a conversation thread with its full message history.

        Args:
            thread_id: Conversation thread ID.
        """
        validate_id(thread_id, name="thread_id")
        safe_tid = quote(str(thread_id), safe="")
        data = await async_with_retry(
            lambda: self._http.get(f"{self._base_path()}/{safe_tid}"),
            self._config.max_retries,
        )
        return Conversation.model_validate(data)
