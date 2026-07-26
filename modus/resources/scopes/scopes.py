"""Read-only scopes resource for the consumption client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Union

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
from ..._generated.models import ComposeSkillContextRequestDto, ScopeDto
from ..._http import AsyncHttpClient, HttpClient
from ..._openapi_invoke import invoke_operation, invoke_operation_async
from ..._pagination import (
    aip_list_params,
    build_aip_page_mapped,
    build_async_aip_page_mapped,
)
from ..._retry import async_with_retry, with_retry
from ..._validation import validate_id, validate_page_size
from ...types.chat import ChatResult
from ...types.context_compose import SkillContextComposition
from ...types.pagination import AsyncPage, Page
from ...types.skills import Skill
from ...types.views import VariationView
from .conversations import (
    SCOPE_CONVERSATION_OPERATIONS,
    AsyncScopeConversationsResource,
    ScopeConversationsOperations,
    ScopeConversationsResource,
)


@dataclass(frozen=True)
class ScopesOperations:
    """Which operationIds / REST segment the scopes consumption resource calls.

    Drives the ``/api/v1/scopes`` surface via :data:`SCOPE_OPERATIONS`.
    """

    resource: str
    list: str
    get: str
    compose: str
    conversations: ScopeConversationsOperations
    stream_session: Callable[..., ChatStream]
    stream_session_async: Callable[..., AsyncChatStream]


SCOPE_OPERATIONS = ScopesOperations(
    resource="scopes",
    list="ScopesController_list",
    get="ScopesController_get",
    compose="ScopeContextController_compose",
    conversations=SCOPE_CONVERSATION_OPERATIONS,
    stream_session=scope_stream_session,
    stream_session_async=scope_stream_session_async,
)


def _parse_scope(raw: dict) -> Skill:
    return ScopeDto.model_validate(raw)


def _scopes_list_params(
    page_size: int,
    page_token: Optional[str],
    search: Optional[str],
    view: Optional[VariationView],
    manager_id: Optional[int],
) -> dict:
    extra: dict = {}
    if search is not None:
        extra["search"] = search
    if view is not None:
        extra["view"] = view
    if manager_id is not None:
        extra["managerId"] = manager_id
    return aip_list_params(page_size, page_token, **extra)


class ScopesResource:
    """
    Read access to Modus scopes.

    client.scopes.list()                               → Page[Skill]
    client.scopes.get(scope_id)                        → Skill
    client.scopes.conversations(scope_id).list()       → Page[ConversationListItem]
    client.scopes.conversations(scope_id).get(thread)  → Conversation

    To create, update, or deploy scopes use modus.management.ModusManagement.
    """

    def __init__(
        self,
        http: HttpClient,
        agent_http: HttpClient,
        config: ModusConfig,
        ops: ScopesOperations = SCOPE_OPERATIONS,
    ) -> None:
        self._http = http
        self._agent_http = agent_http
        self._config = config
        self._ops = ops

    def conversations(self, scope_id: Union[int, str]) -> ScopeConversationsResource:
        """Return the conversations sub-resource scoped to ``scope_id``."""
        return ScopeConversationsResource(self._http, self._config, scope_id, self._ops.conversations)

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        search: Optional[str] = None,
        view: Optional[VariationView] = None,
        manager_id: Optional[int] = None,
    ) -> Page[Skill]:
        """
        List scopes in the organisation.

        Args:
            page_size:   Items per page (default 25).
            page_token:  Opaque token from a previous page's ``next_page_token``.
            search:      Case-insensitive substring filter on the scope name.
            view:        Variation view — ``"active"`` (deployed) or ``"draft"``.
            manager_id:  Return only scopes supervised by this manager scope id.
        """
        validate_page_size(page_size)
        return self._list_page(page_size, page_token, search, view, manager_id)

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        search: Optional[str] = None,
        view: Optional[VariationView] = None,
        manager_id: Optional[int] = None,
    ) -> Page[Skill]:
        params = _scopes_list_params(page_size, page_token, search, view, manager_id)
        data = with_retry(
            lambda: invoke_operation(
                self._http, self._ops.list, query=params
            ),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "scopes",
            _parse_scope,
            lambda cur: self._list_page(page_size, cur, search, view, manager_id),
        )

    def get(
        self,
        scope_id: Union[int, str],
        *,
        view: Optional[VariationView] = None,
    ) -> Skill:
        """
        Retrieve a scope by ID or slug.

        Args:
            view: Variation view — ``"active"`` (deployed) or ``"draft"``.

        Raises:
            NotFoundError: if no scope with this ID/slug exists.
        """
        validate_id(scope_id, name="scope_id")
        query = {} if view is None else {"view": view}
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.get,
                path_params={"id": scope_id},
                query=query or None,
            ),
            self._config.max_retries,
        )
        return _parse_scope(data)

    def chat(
        self,
        scope_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> ChatResult:
        """
        Send a message to a scope and get the complete reply.

        Args:
            scope_id:  Scope ID or slug.
            message:   The message to send.
            model:     Model to run this message with (required). One of the
                       supported model IDs, e.g. ``"claude-sonnet-5"`` or ``"gpt-5.5"``.
            thread_id: Continue an existing conversation; omit to start a new one.

        Returns:
            ChatResult with the reply ``content`` and the ``thread_id`` to continue the conversation.
        """
        return chat_buffered(
            self._http,
            self._ops.resource,
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
        Send a message to a scope and stream the reply token by token.

        Args:
            scope_id:  Scope ID or slug.
            message:   The message to send.
            model:     Model to run this message with (required). One of the
                       supported model IDs, e.g. ``"claude-sonnet-5"`` or ``"gpt-5.5"``.
            thread_id: Continue an existing conversation; omit to start a new one.
            version:   Run a specific variation — ``"published"`` or ``"draft"``.

        Returns:
            ChatStream you can iterate for text chunks; the final result carries the ``thread_id``.
        """
        return self._ops.stream_session(
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
        Return composed context Modus would use for a scope query, without running chat.

        Args:
            scope_id: Scope id or slug.
            message:  Natural-language query used to select context.
            limit:    Optional cap on structured fallback items when no markdown summary exists.
        """
        validate_id(scope_id, name="scope_id")
        body = ComposeSkillContextRequestDto(message=message, limit=limit)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.compose,
                path_params={"id": scope_id},
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return SkillContextComposition.model_validate(data)


class AsyncScopesResource:
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
        ops: ScopesOperations = SCOPE_OPERATIONS,
    ) -> None:
        self._http = http
        self._agent_http = agent_http
        self._config = config
        self._ops = ops

    def conversations(self, scope_id: Union[int, str]) -> AsyncScopeConversationsResource:
        """Return the conversations sub-resource scoped to ``scope_id``."""
        return AsyncScopeConversationsResource(self._http, self._config, scope_id, self._ops.conversations)

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        search: Optional[str] = None,
        view: Optional[VariationView] = None,
        manager_id: Optional[int] = None,
    ) -> AsyncPage[Skill]:
        """
        List scopes in the organisation.

        Args:
            page_size:   Items per page (default 25).
            page_token:  Opaque token from a previous page's ``next_page_token``.
            search:      Case-insensitive substring filter on the scope name.
            view:        Variation view — ``"active"`` (deployed) or ``"draft"``.
            manager_id:  Return only scopes supervised by this manager scope id.
        """
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token, search, view, manager_id)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        search: Optional[str] = None,
        view: Optional[VariationView] = None,
        manager_id: Optional[int] = None,
    ) -> AsyncPage[Skill]:
        params = _scopes_list_params(page_size, page_token, search, view, manager_id)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, self._ops.list, query=params
            ),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "scopes",
            _parse_scope,
            lambda cur: self._list_page(page_size, cur, search, view, manager_id),
        )

    async def get(
        self,
        scope_id: Union[int, str],
        *,
        view: Optional[VariationView] = None,
    ) -> Skill:
        """Retrieve a scope by ID or slug. See the sync ``get`` for argument details."""
        validate_id(scope_id, name="scope_id")
        query = {} if view is None else {"view": view}
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.get,
                path_params={"id": scope_id},
                query=query or None,
            ),
            self._config.max_retries,
        )
        return _parse_scope(data)

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
            self._ops.resource,
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
        return self._ops.stream_session_async(
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
            limit:    Optional cap on structured fallback items when no markdown summary exists.
        """
        validate_id(scope_id, name="scope_id")
        body = ComposeSkillContextRequestDto(message=message, limit=limit)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.compose,
                path_params={"id": scope_id},
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return SkillContextComposition.model_validate(data)
