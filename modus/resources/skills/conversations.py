"""Skill conversations resource — GET /api/v1/skills/:id/conversations"""

from __future__ import annotations

from typing import Optional, Union

from ..._config import ModusConfig
from ..._http import AsyncHttpClient, HttpClient
from ..._openapi_invoke import invoke_operation, invoke_operation_async
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
    def __init__(
        self,
        http: HttpClient,
        config: ModusConfig,
        skill_id: Union[int, str],
    ) -> None:
        self._http = http
        self._config = config
        self._skill_id = skill_id

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> Page[ConversationListItem]:
        """
        List conversation threads for this skill, newest first.

        Args:
            page_size:  Items per page (default 25).
            page_token: Opaque token from a previous page's ``next_page_token``.

        Returns:
            Page[ConversationListItem] — lightweight summaries with
            ``first_message`` and ``message_count``. Call ``.get(thread_id)``
            for the full message history. Use ``.auto_paging_iter()`` to walk
            all pages.
        """
        validate_page_size(page_size)
        return self._list_page(page_size, page_token)

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
    ) -> Page[ConversationListItem]:
        validate_id(self._skill_id, name="skill_id")
        params = aip_list_params(page_size, page_token)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "ConversationsController_list",
                path_params={"id": self._skill_id},
                query=params,
            ),
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
        Retrieve a single conversation thread with its full message history.

        Args:
            thread_id: The conversation thread ID.
        """
        validate_id(self._skill_id, name="skill_id")
        validate_id(thread_id, name="thread_id")
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "ConversationsController_get",
                path_params={"id": self._skill_id, "threadId": thread_id},
            ),
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

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> AsyncPage[ConversationListItem]:
        """List conversation threads for this skill. See ConversationsResource.list."""
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
    ) -> AsyncPage[ConversationListItem]:
        validate_id(self._skill_id, name="skill_id")
        params = aip_list_params(page_size, page_token)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ConversationsController_list",
                path_params={"id": self._skill_id},
                query=params,
            ),
            self._config.max_retries,
        )
        return build_async_aip_page(
            data,
            "conversations",
            ConversationListItem,
            lambda cur: self._list_page(page_size, cur),
        )

    async def get(self, thread_id: str) -> Conversation:
        """Retrieve a single conversation thread. See ConversationsResource.get."""
        validate_id(self._skill_id, name="skill_id")
        validate_id(thread_id, name="thread_id")
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ConversationsController_get",
                path_params={"id": self._skill_id, "threadId": thread_id},
            ),
            self._config.max_retries,
        )
        return Conversation.model_validate(data)
