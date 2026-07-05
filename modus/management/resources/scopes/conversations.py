"""List and retrieve scope conversation threads via the management client."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._pagination import (
    aip_list_params,
    build_aip_page,
    build_async_aip_page,
)
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id, validate_page_size
from modus.types.pagination import AsyncPage, Page

from ...types.conversations import Conversation, ConversationListItem


@dataclass(frozen=True)
class ScopeConversationsOperations:
    """Which scope conversation operationIds this sub-resource calls."""

    list: str
    get: str


SCOPE_CONVERSATION_OPERATIONS = ScopeConversationsOperations(
    list="ScopeConversationsController_list",
    get="ScopeConversationsController_get",
)


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

    def get(self, thread_id: str) -> Conversation:
        """
        Retrieve a conversation thread with its full message history.

        Args:
            thread_id: Conversation thread ID.
        """
        validate_id(self._scope_id, name="scope_id")
        validate_id(thread_id, name="thread_id")
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.get,
                path_params={"id": self._scope_id, "threadId": thread_id},
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
        """
        List conversation threads for this scope, newest first.

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

    async def get(self, thread_id: str) -> Conversation:
        """
        Retrieve a conversation thread with its full message history.

        Args:
            thread_id: Conversation thread ID.
        """
        validate_id(self._scope_id, name="scope_id")
        validate_id(thread_id, name="thread_id")
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.get,
                path_params={"id": self._scope_id, "threadId": thread_id},
            ),
            self._config.max_retries,
        )
        return Conversation.model_validate(data)
