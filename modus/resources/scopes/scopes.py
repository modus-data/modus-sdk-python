"""Read-only scopes resource for the consumption client."""

from __future__ import annotations

from typing import Optional, Union

from modus._generated.resources.consumption.scopes import (
    _AsyncScopesResourceBase,
    _ScopesResourceBase,
)

from ..._chat import AsyncChatSession, ChatSession, start_chat, start_chat_async
from ..._config import ModusConfig
from ..._generated.models import ComposeSkillContextRequestDto
from ..._http import AsyncHttpClient, HttpClient
from ..._openapi_invoke import invoke_operation, invoke_operation_async
from ..._retry import async_with_retry, with_retry
from ..._validation import validate_id
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

    - ``list`` / ``get`` — find an active scope's numeric id
    - ``chat`` — stream a reply from that scope; ``result()`` gives the complete answer
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
        ... ).result()
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
    ) -> ChatSession:
        """
        Chat with a **published scope**. The reply streams live from the agent host:
        iterate ``text_stream`` for tokens, or call ``result()`` for the final answer.

        For the org-wide assistant use ``client.modus.chat`` instead.

        Args:
            scope_id:  Numeric scope id.
            message:   User message text.
            model:     Model id, e.g. ``"claude-sonnet-5.5"``. Unsupported ids raise
                       ``ValueError`` before the request is sent.
            thread_id: Continue an existing conversation; omit to start a new one.

        Returns:
            ``ChatSession``; ``result()`` gives ``content``, ``thread_id`` and ``run_id``.

        Raises:
            ModusError: No agent host is known for a custom ``base_url``.

        Example:
            >>> with client.scopes.chat(scope_id, "What is our ARR trend?", model="claude-sonnet-5.5") as chat:
            ...     for token in chat.text_stream:
            ...         print(token, end="", flush=True)
            >>> follow = client.scopes.chat(
            ...     scope_id,
            ...     "Break that down by segment.",
            ...     model="claude-sonnet-5.5",
            ...     thread_id=chat.result().thread_id,
            ... ).result()
            >>> print(follow.content)
        """
        return start_chat(
            self._agent_http, self._config, "scopes", scope_id, message, model=model, thread_id=thread_id
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
            scope_id: Numeric scope id.
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

    def chat(
        self,
        scope_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> AsyncChatSession:
        """Chat with a scope; ``await`` the session for the final answer. See the sync ``chat``."""
        return start_chat_async(
            self._agent_http, self._config, "scopes", scope_id, message, model=model, thread_id=thread_id
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
            scope_id: Numeric scope id.
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
