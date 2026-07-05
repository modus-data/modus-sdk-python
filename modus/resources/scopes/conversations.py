"""Read scope conversation threads for a published scope."""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class ScopeConversationsOperations:
    """Which scope conversation operationIds this sub-resource calls."""

    list: str
    get: str


SCOPE_CONVERSATION_OPERATIONS = ScopeConversationsOperations(
    list="ScopeConversationsController_list",
    get="ScopeConversationsController_get",
)


def _get_query(
    message_limit: Optional[int],
    before_message_index: Optional[int],
) -> Optional[dict]:
    if before_message_index is not None and message_limit is None:
        raise ValueError("before_message_index requires message_limit")
    query: dict = {}
    if message_limit is not None:
        query["messageLimit"] = message_limit
    if before_message_index is not None:
        query["beforeMessageIndex"] = before_message_index
    return query or None


class ScopeConversationsResource:
    def __init__(
        self,
        http: HttpClient,
        config: ModusConfig,
        scope_id: Union[int, str],
        ops: ScopeConversationsOperations = SCOPE_CONVERSATION_OPERATIONS,
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
    ) -> Page[ConversationListItem]:
        """
        List conversation threads for this scope, newest first.

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
        validate_id(self._scope_id, name="scope_id")
        params = aip_list_params(page_size, page_token)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.list,
                path_params={"id": self._scope_id},
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

    def get(
        self,
        thread_id: str,
        *,
        message_limit: Optional[int] = None,
        before_message_index: Optional[int] = None,
    ) -> Conversation:
        """
        Retrieve a single conversation thread with its full message history.

        Args:
            thread_id: The conversation thread ID.
            message_limit: Return at most this many messages (1-100). Omit
                for the full available conversation.
            before_message_index: Load messages before this zero-based
                index. Requires ``message_limit``.
        """
        validate_id(self._scope_id, name="scope_id")
        validate_id(thread_id, name="thread_id")
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.get,
                path_params={"id": self._scope_id, "threadId": thread_id},
                query=_get_query(message_limit, before_message_index),
            ),
            self._config.max_retries,
        )
        return Conversation.model_validate(data)


class AsyncScopeConversationsResource:
    def __init__(
        self,
        http: AsyncHttpClient,
        config: ModusConfig,
        scope_id: Union[int, str],
        ops: ScopeConversationsOperations = SCOPE_CONVERSATION_OPERATIONS,
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
    ) -> AsyncPage[ConversationListItem]:
        """List conversation threads for this scope. See ScopeConversationsResource.list."""
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
    ) -> AsyncPage[ConversationListItem]:
        validate_id(self._scope_id, name="scope_id")
        params = aip_list_params(page_size, page_token)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.list,
                path_params={"id": self._scope_id},
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

    async def get(
        self,
        thread_id: str,
        *,
        message_limit: Optional[int] = None,
        before_message_index: Optional[int] = None,
    ) -> Conversation:
        """
        Retrieve a single conversation thread with its full message history.

        Args:
            thread_id: The conversation thread ID.
            message_limit: Return at most this many messages (1-100). Omit
                for the full available conversation.
            before_message_index: Load messages before this zero-based
                index. Requires ``message_limit``.
        """
        validate_id(self._scope_id, name="scope_id")
        validate_id(thread_id, name="thread_id")
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.get,
                path_params={"id": self._scope_id, "threadId": thread_id},
                query=_get_query(message_limit, before_message_index),
            ),
            self._config.max_retries,
        )
        return Conversation.model_validate(data)
