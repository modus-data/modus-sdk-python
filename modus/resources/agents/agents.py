"""Agents resource — /api/v1/agents (read-only, consumption SDK)"""

from __future__ import annotations
from typing import Optional, Union
from urllib.parse import quote

from ..._chat import (
    AsyncChatStream,
    ChatStream,
    chat_buffered,
    chat_buffered_async,
    chat_stream_session,
    chat_stream_session_async,
)
from ..._config import ModusConfig
from ..._exceptions import ModusError
from ..._http import AsyncHttpClient, HttpClient
from ..._retry import async_with_retry, with_retry
from ..._validation import validate_id, validate_limit
from ..._wire.agents import _AgentWire
from ...types.agents import Agent
from ...types.chat import ChatResult
from ...types.pagination import AsyncPage, Page
from ._translate import _translate_agent
from .runs import AgentRunsResource, AsyncAgentRunsResource


class AgentsResource:
    """
    Read access to Modus agents.

    client.agents.list() → Page[Agent]
    client.agents.get(agent_id) → Agent

    To create, update, or deploy agents use modus.management.ModusManagement.
    """

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config
        self.runs = AgentRunsResource(http, config)

    def chat(
        self,
        agent_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> ChatResult:
        return chat_buffered(
            self._http,
            "agents",
            agent_id,
            message,
            model=model,
            thread_id=thread_id,
        )

    def chat_stream(
        self,
        agent_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> ChatStream:
        return chat_stream_session(
            self._http,
            "agents",
            agent_id,
            message,
            model=model,
            thread_id=thread_id,
        )

    def list(self, *, limit: int = 20, cursor: Optional[str] = None) -> Page[Agent]:
        """
        List agents in the organisation.

        Args:
            limit:  Items per page (default 20).
            cursor: Pagination cursor from a previous page's next_cursor.
        """
        validate_limit(limit)
        return self._list_page(limit, cursor)

    def _list_page(self, limit: int, cursor: Optional[str]) -> Page[Agent]:
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        data = with_retry(
            lambda: self._http.get("/api/v1/agents", params=params),
            self._config.max_retries,
        )
        if not isinstance(data, dict) or "items" not in data:
            raise ModusError("Unexpected list response shape: missing 'items'")
        items = [_translate_agent(_AgentWire.model_validate(r)) for r in data.get("items", [])]
        next_cursor = data.get("nextCursor") or None
        return Page(
            items=items,
            next_cursor=next_cursor,
            _fetch_page=lambda cur: self._list_page(limit, cur),
        )

    def get(self, agent_id: Union[int, str]) -> Agent:
        """
        Retrieve an agent by ID or slug.

        Raises:
            NotFoundError: if no agent with this ID/slug exists.
        """
        validate_id(agent_id, name="agent_id")
        safe_id = quote(str(agent_id), safe="")
        data = with_retry(
            lambda: self._http.get(f"/api/v1/agents/{safe_id}"),
            self._config.max_retries,
        )
        return _translate_agent(_AgentWire.model_validate(data))


class AsyncAgentsResource:
    """
    Async read access to Modus agents.

    await client.agents.list() → AsyncPage[Agent]
    await client.agents.get(agent_id) → Agent

    To create, update, or deploy agents use modus.management.ModusManagement.
    """

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config
        self.runs = AsyncAgentRunsResource(http, config)

    async def chat(
        self,
        agent_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> ChatResult:
        return await chat_buffered_async(
            self._http,
            "agents",
            agent_id,
            message,
            model=model,
            thread_id=thread_id,
        )

    def chat_stream(
        self,
        agent_id: Union[int, str],
        message: str,
        *,
        model: str,
        thread_id: Optional[str] = None,
    ) -> AsyncChatStream:
        return chat_stream_session_async(
            self._http,
            "agents",
            agent_id,
            message,
            model=model,
            thread_id=thread_id,
        )

    async def list(self, *, limit: int = 20, cursor: Optional[str] = None) -> AsyncPage[Agent]:
        validate_limit(limit)
        return await self._list_page(limit, cursor)

    async def _list_page(self, limit: int, cursor: Optional[str]) -> AsyncPage[Agent]:
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        data = await async_with_retry(
            lambda: self._http.get("/api/v1/agents", params=params),
            self._config.max_retries,
        )
        if not isinstance(data, dict) or "items" not in data:
            raise ModusError("Unexpected list response shape: missing 'items'")
        items = [_translate_agent(_AgentWire.model_validate(r)) for r in data.get("items", [])]
        next_cursor = data.get("nextCursor") or None
        return AsyncPage(
            items=items,
            next_cursor=next_cursor,
            _fetch_page=lambda cur: self._list_page(limit, cur),
        )

    async def get(self, agent_id: Union[int, str]) -> Agent:
        validate_id(agent_id, name="agent_id")
        safe_id = quote(str(agent_id), safe="")
        data = await async_with_retry(
            lambda: self._http.get(f"/api/v1/agents/{safe_id}"),
            self._config.max_retries,
        )
        return _translate_agent(_AgentWire.model_validate(data))
