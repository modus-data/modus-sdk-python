"""Native Modus chat — org-wide assistant (not a single scope)."""

from __future__ import annotations

from typing import Optional

from ..._chat import (
    AsyncChatStream,
    ChatStream,
    modus_chat_buffered,
    modus_chat_buffered_async,
    modus_stream_session,
    modus_stream_session_async,
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
    Chat with Modus — the org-wide assistant with full environment context and tools.

    Prefer this over ``client.scopes.chat`` when the question is not tied to one
    published scope. Construct the client with ``modus.Modus()`` (reads
    ``MODUS_API_KEY``).

    When to use which method:

    - ``chat`` — one complete reply (simplest).
    - ``chat_stream`` — print tokens as they arrive.
    - ``get_context`` — preview composed context without running a chat turn.
    - ``conversations`` — list/get prior Modus threads.

    Example:
        >>> import modus
        >>> client = modus.Modus()
        >>> result = client.modus.chat(
        ...     "What tables describe revenue?",
        ...     model="claude-sonnet-5",
        ... )
        >>> print(result.content)
        >>> print(result.thread_id)  # pass as thread_id on the next message
    """

    def __init__(self, http: HttpClient, agent_http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._agent_http = agent_http
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
        Send a message to Modus and wait for the complete reply.

        Args:
            message:   User message text.
            model:     Model id, e.g. ``"claude-sonnet-5"``. Unsupported ids raise
                       ``ValueError`` before the request is sent.
            thread_id: Continue an existing conversation; omit to start a new thread.

        Returns:
            ``ChatResult`` with:

            - ``content`` — final assistant text
            - ``thread_id`` — pass to the next ``chat`` / ``chat_stream`` call
            - ``run_id`` — opaque id for logging

        Raises:
            AuthenticationError: Invalid or missing API key.
            NotFoundError: ``thread_id`` does not exist.
            APIError: Upstream request failure.

        Example:
            >>> result = client.modus.chat(
            ...     "What tables describe revenue?",
            ...     model="claude-sonnet-5",
            ... )
            >>> print(result.content, result.thread_id)
            >>> follow = client.modus.chat(
            ...     "Break that down by region.",
            ...     model="claude-sonnet-5",
            ...     thread_id=result.thread_id,
            ... )
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
        """
        Stream a Modus reply token by token (SSE).

        The HTTP request starts when you consume ``text_stream`` or
        ``event_stream``. Always use the context manager and iterate.

        Args:
            message:   User message text.
            model:     Model id, e.g. ``"claude-sonnet-5"``.
            thread_id: Continue an existing conversation; omit to start new.

        Returns:
            ``ChatStream``. After the stream finishes,
            ``stream.get_final_result()`` exposes ``content`` and ``thread_id``.

        Example:
            >>> with client.modus.chat_stream(
            ...     "Summarize ARR in three bullets.",
            ...     model="claude-sonnet-5",
            ... ) as stream:
            ...     for token in stream.text_stream:
            ...         print(token, end="", flush=True)
            >>> print(stream.get_final_result().thread_id)
        """
        return modus_stream_session(
            self._agent_http, message, model=model, thread_id=thread_id
        )

    def get_context(
        self,
        message: str,
        *,
        limit: Optional[int] = None,
    ) -> SkillContextComposition:
        """
        Compose full-environment context for an intent without running chat.

        Use this to inspect what Modus would retrieve before (or instead of)
        calling ``chat``.

        Args:
            message: Natural-language intent used to select context.
            limit:   Optional cap on structured fallback items when no markdown
                     summary exists.

        Returns:
            Composition object (includes counts / session metadata used by the
            product UI). Prefer ``chat`` when you need an assistant reply.

        Example:
            >>> ctx = client.modus.get_context(
            ...     "What tables describe revenue?",
            ...     limit=5,
            ... )
            >>> print(ctx.original_count, ctx.session_id)
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
    """
    Async native Modus chat (same methods as ``ModusResource``).

    Example:
        >>> async with modus.AsyncModus() as client:
        ...     result = await client.modus.chat(
        ...         "Hello",
        ...         model="claude-sonnet-5",
        ...     )
        ...     print(result.content)
    """

    def __init__(self, http: AsyncHttpClient, agent_http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._agent_http = agent_http
        self._config = config
        self.conversations = AsyncModusConversationsResource(http, config)

    async def chat(
        self,
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> ChatResult:
        """
        Send a message to Modus and wait for the complete reply.

        Args:
            message:   User message text.
            model:     Model id, e.g. ``"claude-sonnet-5"``.
            thread_id: Continue an existing conversation; omit to start new.

        Returns:
            ``ChatResult`` with ``content``, ``thread_id``, and ``run_id``.
        """
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
        """
        Stream a Modus reply token by token (async).

        Args:
            message:   User message text.
            model:     Model id, e.g. ``"claude-sonnet-5"``.
            thread_id: Continue an existing conversation; omit to start new.

        Returns:
            ``AsyncChatStream`` — ``async for token in stream.text_stream``.
        """
        return modus_stream_session_async(
            self._agent_http, message, model=model, thread_id=thread_id
        )

    async def get_context(
        self,
        message: str,
        *,
        limit: Optional[int] = None,
    ) -> SkillContextComposition:
        """
        Compose full-environment context for an intent without running chat.

        Args:
            message: Natural-language intent used to select context.
            limit:   Optional cap on structured fallback items.
        """
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
