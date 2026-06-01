"""Skill conversations resource — GET /api/v1/skills/:id/conversations"""

from __future__ import annotations
from typing import Optional, Union
from urllib.parse import quote

from ..._config import ModusConfig
from ..._http import AsyncHttpClient, HttpClient
from ..._pagination import (
    aip_list_params,
    build_aip_page,
    build_async_aip_page,
)
from ..._retry import async_with_retry, with_retry
from ..._validation import validate_id, validate_page_size
from ...types.conversations import Conversation, ConversationListItem
from ...types.pagination import AsyncPage, Page


class ConversationsResource:
    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(
        self,
        skill_id: Union[int, str],
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> Page[ConversationListItem]:
        """
        List all Modus conversation threads for a skill, newest first.

        Args:
            skill_id:   Modus skill ID or slug.
            page_size:  Maximum number of items to return (default 25).
            page_token: Token from a previous page's ``next_page_token``; omit for the first page.

        Returns:
            Page[ConversationListItem] — lightweight summaries with
            ``first_message`` and ``message_count``. Call
            ``conversations.get(skill_id, item.thread_id)`` for the full
            message history. Use ``.auto_paging_iter()`` to walk all pages.
        """
        validate_id(skill_id, name="skill_id")
        validate_page_size(page_size)
        return self._list_page(skill_id, page_size, page_token)

    def _list_page(
        self,
        skill_id: Union[int, str],
        page_size: int,
        page_token: Optional[str],
    ) -> Page[ConversationListItem]:
        params = aip_list_params(page_size, page_token)
        safe_skill_id = quote(str(skill_id), safe="")
        data = with_retry(
            lambda: self._http.get(
                f"/api/v1/skills/{safe_skill_id}/conversations", params=params
            ),
            self._config.max_retries,
        )
        return build_aip_page(
            data,
            "conversations",
            ConversationListItem,
            lambda cur: self._list_page(skill_id, page_size, cur),
        )

    def get(self, skill_id: Union[int, str], thread_id: str) -> Conversation:
        """
        Retrieve a Modus conversation thread with its full message history.

        Args:
            skill_id:  Modus skill ID or slug.
            thread_id: Modus conversation thread ID.
        """
        validate_id(skill_id, name="skill_id")
        safe_skill_id = quote(str(skill_id), safe="")
        safe_thread_id = quote(str(thread_id), safe="")
        data = with_retry(
            lambda: self._http.get(
                f"/api/v1/skills/{safe_skill_id}/conversations/{safe_thread_id}"
            ),
            self._config.max_retries,
        )
        return Conversation.model_validate(data)


class AsyncConversationsResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list(
        self,
        skill_id: Union[int, str],
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> AsyncPage[ConversationListItem]:
        """
        List all Modus conversation threads for a skill, newest first.

        Args:
            skill_id:   Modus skill ID or slug.
            page_size:  Maximum number of items to return (default 25).
            page_token: Token from a previous page's ``next_page_token``; omit for the first page.
        """
        validate_id(skill_id, name="skill_id")
        validate_page_size(page_size)
        return await self._list_page(skill_id, page_size, page_token)

    async def _list_page(
        self,
        skill_id: Union[int, str],
        page_size: int,
        page_token: Optional[str],
    ) -> AsyncPage[ConversationListItem]:
        params = aip_list_params(page_size, page_token)
        safe_skill_id = quote(str(skill_id), safe="")
        data = await async_with_retry(
            lambda: self._http.get(
                f"/api/v1/skills/{safe_skill_id}/conversations", params=params
            ),
            self._config.max_retries,
        )
        return build_async_aip_page(
            data,
            "conversations",
            ConversationListItem,
            lambda cur: self._list_page(skill_id, page_size, cur),
        )

    async def get(self, skill_id: Union[int, str], thread_id: str) -> Conversation:
        """
        Retrieve a Modus conversation thread with its full message history.

        Args:
            skill_id:  Modus skill ID or slug.
            thread_id: Modus conversation thread ID.
        """
        validate_id(skill_id, name="skill_id")
        safe_skill_id = quote(str(skill_id), safe="")
        safe_thread_id = quote(str(thread_id), safe="")
        data = await async_with_retry(
            lambda: self._http.get(
                f"/api/v1/skills/{safe_skill_id}/conversations/{safe_thread_id}"
            ),
            self._config.max_retries,
        )
        return Conversation.model_validate(data)
