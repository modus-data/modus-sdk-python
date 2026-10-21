"""Read-only scopes resource for the consumption client."""

from __future__ import annotations

from typing import Optional, Union

from modus._generated.resources.consumption.scopes import (
    _AsyncScopesResourceBase,
    _ScopesResourceBase,
)

from ..._chat import (
    AsyncChatStream,
    ChatStream,
    RunVersion,
    chat_buffered,
    chat_buffered_async,
    scope_stream_session,
    scope_stream_session_async,
)
from ..._config import ModusConfig
from ..._generated.models import ComposeSkillContextRequestDto
from ..._http import AsyncHttpClient, HttpClient
from ..._openapi_invoke import invoke_operation, invoke_operation_async
from ..._retry import async_with_retry, with_retry
from ..._validation import validate_id
from ...types.chat import ChatResult
from ...types.context_compose import SkillContextComposition
from .conversations import (
    AsyncScopeConversationsResource,
    ScopeConversationsResource,
)


class ScopesResource(_ScopesResourceBase):
    """
    Read and chat with published **scopes** (consumption client).

    Construct with ``modus.Modus()`` (reads ``MODUS_API_KEY``). To create or
    deploy scopes use ``modus.management.ModusManagement``.

    When to use which method:

    - ``list`` / ``get`` — find an active scope id or slug
    - ``chat`` — one complete reply from that scope
    - ``chat_stream`` — print tokens as they arrive
    - ``get_context`` — preview composed context without chatting
    - ``conversations(scope_id)`` — list/get prior threads for that scope

    For the org-wide assistant use ``client.modus`` instead.

    Example:
        >>> import modus
        >>> client = modus.Modus()
        >>> scope = next(
        ...     s for s in client.scopes.list().auto_paging_iter() if s.status == "active"
        ... )
        >>> result = client.scopes.chat(
        ...     scope.id, "What is our ARR trend?", model="claude-sonnet-5"
        ... )
        >>> print(result.content)
    """

    def __init__(
        self,
        http: HttpClient,
        agent_http: HttpClient,
        config: ModusConfig,
    ) -> None:
        super().__init__(http, config)
        self._agent_http = agent_http

    def conversations(self, scope_id: Union[int, str]) -> ScopeConversationsResource:
        """
        Return the conversations sub-resource for one scope.

        Example:
            >>> for row in client.scopes.conversations(scope_id).list(page_size=10):
            ...     print(row.thread_id, row.first_message)
        """
        return ScopeConversationsResource(self._http, self._config, scope_id)

    def chat(
        self,
        scope_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> ChatResult:
        """
        Send a message to a **published scope** and wait for the complete reply.

        For the org-wide assistant use ``client.modus.chat`` instead.

        Args:
            scope_id:  Scope numeric id or slug (must be active/deployed for chat).
            message:   User message text.
            model:     Model id, e.g. ``"claude-sonnet-5"``. Unsupported ids raise
                       ``ValueError`` before the request is sent.
            thread_id: Continue an existing conversation; omit to start a new one.

        Returns:
            ``ChatResult`` with ``content``, ``thread_id``, and ``run_id``.

        Raises:
            NotFoundError: Scope or ``thread_id`` does not exist.
            AuthenticationError: Invalid or missing API key.

        Example:
            >>> result = client.scopes.chat(
            ...     scope_id,
            ...     "What is our ARR trend?",
            ...     model="claude-sonnet-5",
            ... )
            >>> print(result.content)
            >>> follow = client.scopes.chat(
            ...     scope_id,
            ...     "Break that down by segment.",
            ...     model="claude-sonnet-5",
            ...     thread_id=result.thread_id,
            ... )
        """
        return chat_buffered(
            self._http,
            "scopes",
            scope_id,
            message,
            model=model,
            thread_id=thread_id,
        )

    def chat_stream(
        self,
        scope_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
        version: Optional[RunVersion] = None,
    ) -> ChatStream:
        """
        Stream a scope reply token by token (SSE).

        The HTTP request starts when you consume ``text_stream`` or
        ``event_stream``. Always use the context manager and iterate.

        Args:
            scope_id:  Scope numeric id or slug.
            message:   User message text.
            model:     Model id, e.g. ``"claude-sonnet-5"``.
            thread_id: Continue an existing conversation; omit to start new.
            version:   Run a specific variation — ``"published"`` or ``"draft"``.

        Returns:
            ``ChatStream``. After iteration,
            ``stream.get_final_result()`` exposes ``content`` and ``thread_id``.

        Example:
            >>> with client.scopes.chat_stream(
            ...     scope_id,
            ...     "Summarize in three bullets.",
            ...     model="claude-sonnet-5",
            ... ) as stream:
            ...     for token in stream.text_stream:
            ...         print(token, end="", flush=True)
        """
        return scope_stream_session(
            self._agent_http,
            scope_id,
            message,
            model=model,
            thread_id=thread_id,
            version=version,
        )

    def get_context(
        self,
        scope_id: Union[int, str],
        message: str,
        *,
        limit: Optional[int] = None,
    ) -> SkillContextComposition:
        """
        Compose context this scope would use for an intent, without running chat.

        Args:
            scope_id: Scope numeric id or slug.
            message:  Natural-language query used to select context.
            limit:    Maximum context items to return. Omit to return all
                      selected items.

        Returns:
            Composed context text and selection metadata. The text is usually
            Markdown but may be the documented JSON fallback. Large bodies are
            bounded inline previews; this REST method has no file-reference or
            full-content fetch operation.

        Example:
            >>> ctx = client.scopes.get_context(
            ...     scope_id,
            ...     "Which tables describe churn?",
            ...     limit=5,
            ... )
            >>> print(ctx.original_count, ctx.session_id)
        """
        validate_id(scope_id, name="scope_id")
        body = ComposeSkillContextRequestDto(message=message, limit=limit)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopeContextController_compose",
                path_params={"id": scope_id},
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return SkillContextComposition.model_validate(data)


class AsyncScopesResource(_AsyncScopesResourceBase):
    """
    Async read access to Modus scopes.

    await client.scopes.list()                               → AsyncPage[Skill]
    await client.scopes.get(scope_id)                        → Skill
    await client.scopes.conversations(scope_id).list()       → AsyncPage[ConversationListItem]

    To create, update, or deploy scopes use modus.management.ModusManagement.
    """

    def __init__(
        self,
        http: AsyncHttpClient,
        agent_http: AsyncHttpClient,
        config: ModusConfig,
    ) -> None:
        super().__init__(http, config)
        self._agent_http = agent_http

    def conversations(self, scope_id: Union[int, str]) -> AsyncScopeConversationsResource:
        """Return the conversations sub-resource scoped to ``scope_id``."""
        return AsyncScopeConversationsResource(self._http, self._config, scope_id)

    async def chat(
        self,
        scope_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> ChatResult:
        """Send a message to a scope and get the complete reply. See the sync ``chat`` for argument details."""
        return await chat_buffered_async(
            self._http,
            "scopes",
            scope_id,
            message,
            model=model,
            thread_id=thread_id,
        )

    def chat_stream(
        self,
        scope_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
        version: Optional[RunVersion] = None,
    ) -> AsyncChatStream:
        """Stream a scope reply token by token. See the sync ``chat_stream`` for argument details."""
        return scope_stream_session_async(
            self._agent_http,
            scope_id,
            message,
            model=model,
            thread_id=thread_id,
            version=version,
        )

    async def get_context(
        self,
        scope_id: Union[int, str],
        message: str,
        *,
        limit: Optional[int] = None,
    ) -> SkillContextComposition:
        """
        Return composed context Modus would use for a scope query, without running chat.

        Args:
            scope_id: Scope id or slug.
            message:  Natural-language query used to select context.
            limit:    Maximum context items to return. Omit to return all selected items.
        """
        validate_id(scope_id, name="scope_id")
        body = ComposeSkillContextRequestDto(message=message, limit=limit)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopeContextController_compose",
                path_params={"id": scope_id},
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return SkillContextComposition.model_validate(data)
