"""Read scope conversation threads for a published scope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from modus._generated.resources.consumption.scopes.conversations import (
    _AsyncScopesConversationsResourceBase,
    _ScopesConversationsResourceBase,
)

from ..._config import ModusConfig
from ..._http import AsyncHttpClient, HttpClient
from ..._openapi_invoke import invoke_operation, invoke_operation_async
from ..._retry import async_with_retry, with_retry
from ..._validation import validate_id
from ...types.conversations import Conversation


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


class ScopeConversationsResource(_ScopesConversationsResourceBase):
    """
    Prior chat threads for one published scope.

    Obtained via ``client.scopes.conversations(scope_id)``. List summaries
    first, then ``get(thread_id)`` for the full message history.
    """

    def __init__(
        self,
        http: HttpClient,
        config: ModusConfig,
        scope_id: Union[int, str],
        ops: ScopeConversationsOperations = SCOPE_CONVERSATION_OPERATIONS,
    ) -> None:
        super().__init__(http, config, scope_id, ops)
        self._ops: ScopeConversationsOperations = ops

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

        Returns:
            ``Conversation`` with ``messages`` (role + content).

        Raises:
            NotFoundError: Scope or thread does not exist.

        Example:
            >>> thread = client.scopes.conversations(scope_id).get(row.thread_id)
            >>> for msg in thread.messages:
            ...     print(msg.type, str(msg.content)[:80])
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


class AsyncScopeConversationsResource(_AsyncScopesConversationsResourceBase):
    def __init__(
        self,
        http: AsyncHttpClient,
        config: ModusConfig,
        scope_id: Union[int, str],
        ops: ScopeConversationsOperations = SCOPE_CONVERSATION_OPERATIONS,
    ) -> None:
        super().__init__(http, config, scope_id, ops)
        self._ops: ScopeConversationsOperations = ops

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
