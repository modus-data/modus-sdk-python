"""Native Modus chat — org-wide assistant (not a single scope)."""

from __future__ import annotations

from typing import Optional

from ..._chat import AsyncChatSession, ChatSession, start_chat, start_chat_async
from ..._config import ModusConfig
from ..._generated.models import ModusContextRequestDto
from ..._http import AsyncHttpClient, HttpClient
from ..._openapi_invoke import invoke_operation, invoke_operation_async
from ..._retry import async_with_retry, with_retry
from ...types.context_compose import SkillContextComposition
from .conversations import AsyncModusConversationsResource, ModusConversationsResource


class ModusResource:
    """
    Chat with Modus — the org-wide assistant with full environment context and tools.

    Prefer this over ``client.scopes.chat`` when the question is not tied to one
    published scope. Construct the client with ``modus.Modus()`` (reads
    ``MODUS_API_KEY``).

    When to use which method:

    - ``chat`` — stream a reply live; ``result()`` gives the complete answer.
    - ``get_context`` — preview composed context without running a chat turn.
    - ``conversations`` — list/get prior Modus threads.

    Example:
        >>> import modus
        >>> client = modus.Modus()
        >>> result = client.modus.chat(
        ...     "What tables describe revenue?",
        ...     model="claude-sonnet-5",
        ... ).result()
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
    ) -> ChatSession:
        """
        Chat with Modus, the org-wide assistant. The reply streams live from the
        agent host: iterate ``text_stream`` for tokens, or call ``result()`` for
        the final answer.

        Args:
            message:   User message text.
            model:     Model id, e.g. ``"claude-sonnet-5.5"``. Unsupported ids raise
                       ``ValueError`` before the request is sent.
            thread_id: Continue an existing conversation; omit to start a new one.

        Returns:
            ``ChatSession``; ``result()`` gives ``content``, ``thread_id`` and ``run_id``,
            plus ``approval`` when the run stopped for a decision.

        Raises:
            ModusError: No agent host is known for a custom ``base_url``.

        Example:
            >>> result = client.modus.chat("What tables describe revenue?", model="claude-sonnet-5.5").result()
            >>> print(result.content)
            >>> with client.modus.chat("Break that down by region.", model="claude-sonnet-5.5",
            ...                        thread_id=result.thread_id) as chat:
            ...     for token in chat.text_stream:
            ...         print(token, end="", flush=True)
        """
        return start_chat(
            self._agent_http, self._config, "modus", None, message, model=model, thread_id=thread_id
        )

    def get_context(
        self,
        message: str,
        *,
        limit: Optional[int] = None,
    ) -> SkillContextComposition:
        """
        Compose full-environment context for an intent without running chat.

        Runs on the agent host, like ``chat``, so a compose may take up to 90
        seconds; keep ``timeout`` above that. A compose still running at 90
        seconds raises with ``UPSTREAM_TIMEOUT`` (HTTP 504).

        Use this to inspect what Modus would retrieve before (or instead of)
        calling ``chat``.

        Args:
            message: Natural-language intent used to select context.
            limit:   Maximum context items to return. Omit to return all
                     selected items.

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
                "ModusContextComposeController_compose",
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

    def chat(
        self,
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> AsyncChatSession:
        """Chat with Modus; ``await`` the session for the final answer. See the sync ``chat``."""
        return start_chat_async(
            self._agent_http, self._config, "modus", None, message, model=model, thread_id=thread_id
        )

    async def get_context(
        self,
        message: str,
        *,
        limit: Optional[int] = None,
    ) -> SkillContextComposition:
        """
        Compose full-environment context for an intent without running chat.

        Runs on the agent host, like ``chat``, so a compose may take up to 90
        seconds; keep ``timeout`` above that. A compose still running at 90
        seconds raises with ``UPSTREAM_TIMEOUT`` (HTTP 504).

        Args:
            message: Natural-language intent used to select context.
            limit:   Maximum context items to return. Omit to return all
                     selected items.
        """
        body = ModusContextRequestDto(message=message, limit=limit)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ModusContextComposeController_compose",
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return SkillContextComposition.model_validate(data)
