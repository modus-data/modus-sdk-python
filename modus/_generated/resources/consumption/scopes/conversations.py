# Auto-generated from the Modus API schema. Do not edit by hand.

from __future__ import annotations

from typing import Optional, Protocol, Union

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._pagination import aip_list_params, build_aip_page_mapped, build_async_aip_page_mapped
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id, validate_page_size
from modus.types.conversations import ConversationListItem
from modus.types.pagination import AsyncPage, Page


class _Operations(Protocol):
    @property
    def list(self) -> str: ...


class _ScopesConversationsResourceBase:
    """Generated base for the consumption ``scopes.conversations`` resource."""

    def __init__(
        self,
        http: HttpClient,
        config: ModusConfig,
        scope_id: Union[int, str],
        ops: _Operations,
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
        source: Optional[str] = None,
        source_ref: Optional[str] = None,
    ) -> Page[ConversationListItem]:
        """
        List scope conversations.

        Returns a page of conversation summaries (most recently updated first) for a scope. Use
        ``id=0`` for your cross-scope recent history. Pass ``next_page_token`` as ``page_token`` to
        fetch the next page.

        **Requires:** ``scopes:read``

        Args:
            page_size: Items per page. Defaults to 25.
            page_token: Opaque page token from a previous response's ``next_page_token``. Omit for
                the first page.
            source: Return only conversations started from this UI surface.
            source_ref: Narrow ``source`` to one instance of that surface — for
                ``dashboard_copilot`` or ``dashboard_assistant``, a dashboard id (both scope
                conversation history per dashboard). Requires ``source``; sent alone it is a 422.

        Returns:
            A page of conversations.

        Example:
            >>> for row in client.scopes.conversations(scope_id).list(page_size=10):
            ...     print(row.thread_id, row.first_message, row.message_count)
        """
        validate_page_size(page_size)
        return self._list_page(page_size, page_token, source, source_ref)

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        source: Optional[str],
        source_ref: Optional[str],
    ) -> Page[ConversationListItem]:
        validate_id(self._scope_id, name="scope_id")
        params = aip_list_params(page_size, page_token)
        if source is not None:
            params["source"] = source
        if source_ref is not None:
            params["sourceRef"] = source_ref
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.list,
                path_params={"id": self._scope_id},
                query=params,
            ),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "conversations",
            ConversationListItem.model_validate,
            lambda cur: self._list_page(page_size, cur, source, source_ref),
        )


class _AsyncScopesConversationsResourceBase:
    """Generated base for the consumption ``scopes.conversations`` resource."""

    def __init__(
        self,
        http: AsyncHttpClient,
        config: ModusConfig,
        scope_id: Union[int, str],
        ops: _Operations,
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
        source: Optional[str] = None,
        source_ref: Optional[str] = None,
    ) -> AsyncPage[ConversationListItem]:
        """
        List scope conversations.

        Returns a page of conversation summaries (most recently updated first) for a scope. Use
        ``id=0`` for your cross-scope recent history. Pass ``next_page_token`` as ``page_token`` to
        fetch the next page.

        **Requires:** ``scopes:read``

        Args:
            page_size: Items per page. Defaults to 25.
            page_token: Opaque page token from a previous response's ``next_page_token``. Omit for
                the first page.
            source: Return only conversations started from this UI surface.
            source_ref: Narrow ``source`` to one instance of that surface — for
                ``dashboard_copilot`` or ``dashboard_assistant``, a dashboard id (both scope
                conversation history per dashboard). Requires ``source``; sent alone it is a 422.

        Returns:
            A page of conversations.
        """
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token, source, source_ref)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        source: Optional[str],
        source_ref: Optional[str],
    ) -> AsyncPage[ConversationListItem]:
        validate_id(self._scope_id, name="scope_id")
        params = aip_list_params(page_size, page_token)
        if source is not None:
            params["source"] = source
        if source_ref is not None:
            params["sourceRef"] = source_ref
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.list,
                path_params={"id": self._scope_id},
                query=params,
            ),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "conversations",
            ConversationListItem.model_validate,
            lambda cur: self._list_page(page_size, cur, source, source_ref),
        )
