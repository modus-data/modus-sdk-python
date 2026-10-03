"""Read Modus conversation threads (cross-skill and direct Modus)."""

from __future__ import annotations

from typing import Literal, Optional

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

ConversationKind = Literal["all", "modus", "scopes"]
_ALLOWED_KINDS = frozenset({"all", "modus", "scopes"})


def _list_params(
    page_size: int,
    page_token: Optional[str],
    kind: Optional[ConversationKind],
    source: Optional[str] = None,
    source_ref: Optional[str] = None,
) -> dict:
    if kind is not None and kind not in _ALLOWED_KINDS:
        raise ValueError(f"kind must be one of {sorted(_ALLOWED_KINDS)}, got {kind!r}")
    extra: dict = {}
    if kind is not None:
        extra["kind"] = kind
    if source is not None:
        extra["source"] = source
    if source_ref is not None:
        extra["sourceRef"] = source_ref
    return aip_list_params(page_size, page_token, **extra)


class ModusConversationsResource:
    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        kind: Optional[ConversationKind] = None,
        source: Optional[str] = None,
        source_ref: Optional[str] = None,
    ) -> Page[ConversationListItem]:
        """
        List conversations across Modus and scopes.

        Args:
            page_size:  Items per page (default 25).
            page_token: Opaque token from a previous page's ``next_page_token``.
            kind:       ``"modus"`` for direct Modus chats only; ``"scopes"``
                        to exclude them; omit or ``"all"`` for everything.
            source:     Restrict to conversations started from this UI surface
                        (e.g. ``"context_chat"``, ``"dashboard_copilot"``, ``"slack"``).
                        Only valid with an omitted ``kind`` or ``kind="all"``; the
                        API raises :class:`~modus.UnprocessableError` (422) if
                        combined with ``kind="modus"`` or ``kind="scopes"``.
            source_ref: Narrow ``source`` to one instance of that surface — for
                        ``"dashboard_copilot"`` or ``"dashboard_assistant"``, a dashboard id
                        (both scope conversation history per dashboard). Requires ``source``;
                        the API raises :class:`~modus.UnprocessableError` (422) if
                        sent on its own. Conversations recorded before this filter
                        shipped carry no instance key and never match it.
        """
        validate_page_size(page_size)
        return self._list_page(page_size, page_token, kind, source, source_ref)

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        kind: Optional[ConversationKind],
        source: Optional[str] = None,
        source_ref: Optional[str] = None,
    ) -> Page[ConversationListItem]:
        params = _list_params(page_size, page_token, kind, source, source_ref)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "ModusConversationsController_list",
                query=params,
            ),
            self._config.max_retries,
        )
        return build_aip_page(
            data,
            "conversations",
            ConversationListItem,
            lambda cur: self._list_page(page_size, cur, kind, source, source_ref),
        )

    def get(self, thread_id: str) -> Conversation:
        """Retrieve a conversation thread with full message history."""
        validate_id(thread_id, name="thread_id")
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "ModusConversationsController_get",
                path_params={"threadId": thread_id},
            ),
            self._config.max_retries,
        )
        return Conversation.model_validate(data)


class AsyncModusConversationsResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        kind: Optional[ConversationKind] = None,
        source: Optional[str] = None,
        source_ref: Optional[str] = None,
    ) -> AsyncPage[ConversationListItem]:
        """List conversations across Modus and scopes. See the sync ``list`` for argument details."""
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token, kind, source, source_ref)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        kind: Optional[ConversationKind],
        source: Optional[str] = None,
        source_ref: Optional[str] = None,
    ) -> AsyncPage[ConversationListItem]:
        params = _list_params(page_size, page_token, kind, source, source_ref)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ModusConversationsController_list",
                query=params,
            ),
            self._config.max_retries,
        )
        return build_async_aip_page(
            data,
            "conversations",
            ConversationListItem,
            lambda cur: self._list_page(page_size, cur, kind, source, source_ref),
        )

    async def get(self, thread_id: str) -> Conversation:
        """Retrieve a conversation thread with full message history. See the sync ``get`` for argument details."""
        validate_id(thread_id, name="thread_id")
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ModusConversationsController_get",
                path_params={"threadId": thread_id},
            ),
            self._config.max_retries,
        )
        return Conversation.model_validate(data)
