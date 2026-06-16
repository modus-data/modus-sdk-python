"""Native Modus chat — org-wide assistant, not a skill."""

from __future__ import annotations

from typing import Optional

from ..._chat import (
    AsyncChatStream,
    ChatStream,
    modus_chat_buffered,
    modus_chat_buffered_async,
    modus_chat_stream_session,
    modus_chat_stream_session_async,
)
from ..._config import ModusConfig
from ..._generated.models import ModusContextRequestDto
from ..._http import AsyncHttpClient, HttpClient
from ..._openapi_invoke import invoke_operation, invoke_operation_async
from ..._retry import async_with_retry, with_retry
from ...types.chat import ChatResult
from ...types.context_compose import SkillContextComposition
from .conversations import AsyncModusConversationsResource, ModusConversationsResource


class ModusResource:
    """
    Chat with Modus — your org-wide assistant with full context and tools.

    client.modus.chat("…", model="claude-sonnet-4.6")
    client.modus.conversations.list(kind="modus")
    client.modus.get_context("What tables describe churn?")
    """

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config
        self.conversations = ModusConversationsResource(http, config)

    def chat(
        self,
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> ChatResult:
        """
        Send a message to Modus and get the complete reply.

        Args:
            message:   The message to send.
            model:     Model id, e.g. ``"claude-sonnet-4.6"``.
            thread_id: Continue an existing conversation; omit to start new.
        """
        return modus_chat_buffered(
            self._http, message, model=model, thread_id=thread_id
        )

    def chat_stream(
        self,
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> ChatStream:
        """Stream a Modus reply token by token."""
        return modus_chat_stream_session(
            self._http, message, model=model, thread_id=thread_id
        )

    def get_context(
        self,
        message: str,
        *,
        limit: Optional[int] = None,
    ) -> SkillContextComposition:
        """
        Return composed full-environment context for an intent, without running chat.
        """
        body = ModusContextRequestDto(message=message, limit=limit)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "ModusContextController_compose",
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return SkillContextComposition.model_validate(data)


class AsyncModusResource:
    """Async native Modus chat."""

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config
        self.conversations = AsyncModusConversationsResource(http, config)

    async def chat(
        self,
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> ChatResult:
        return await modus_chat_buffered_async(
            self._http, message, model=model, thread_id=thread_id
        )

    def chat_stream(
        self,
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> AsyncChatStream:
        return modus_chat_stream_session_async(
            self._http, message, model=model, thread_id=thread_id
        )

    async def get_context(
        self,
        message: str,
        *,
        limit: Optional[int] = None,
    ) -> SkillContextComposition:
        body = ModusContextRequestDto(message=message, limit=limit)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ModusContextController_compose",
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return SkillContextComposition.model_validate(data)
