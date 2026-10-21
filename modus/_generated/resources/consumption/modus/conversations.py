# Auto-generated from the Modus API schema. Do not edit by hand.

from __future__ import annotations

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id
from modus.types.conversations import Conversation


class _ModusConversationsResourceBase:
    """Generated base for the consumption ``modus.conversations`` resource."""

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def get(self, thread_id: str) -> Conversation:
        """
        Get a Modus conversation.

        Returns the full message history for a conversation thread.

        **Requires:** ``scopes:read``

        Args:
            thread_id: Thread id from a conversation list or chat response.
        """
        validate_id(thread_id, name="thread_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ModusConversationsController_get",
                path_params={"threadId": thread_id},
            ),
            self._config.max_retries,
        )
        return Conversation.model_validate(raw)


class _AsyncModusConversationsResourceBase:
    """Generated base for the consumption ``modus.conversations`` resource."""

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def get(self, thread_id: str) -> Conversation:
        """
        Get a Modus conversation.

        Returns the full message history for a conversation thread.

        **Requires:** ``scopes:read``

        Args:
            thread_id: Thread id from a conversation list or chat response.
        """
        validate_id(thread_id, name="thread_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ModusConversationsController_get",
                path_params={"threadId": thread_id},
            ),
            self._config.max_retries,
        )
        return Conversation.model_validate(raw)
