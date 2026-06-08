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
from ..._http import AsyncHttpClient, HttpClient
from ..._pagination import (
    aip_list_params,
    build_aip_page_mapped,
    build_async_aip_page_mapped,
)
from ..._retry import async_with_retry, with_retry
from ..._validation import validate_id, validate_page_size
from ..._wire.agents import _AgentWire
from ...types.agents import Agent
from ...types.chat import ChatResult
from ...types.pagination import AsyncPage, Page
from ._translate import _translate_agent
from .runs import AgentRunsResource, AsyncAgentRunsResource


def _map_agent(raw: dict) -> Agent:
    return _translate_agent(_AgentWire.model_validate(raw))


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
        """
        Send a message to an agent and get the complete reply.

        Args:
            agent_id:  Agent ID or slug.
            message:   The message to send.
            model:     Model to run this message with (required). One of the
                       supported model IDs, e.g. ``"claude-sonnet-4.6"`` or ``"gpt-5.5"``.
            thread_id: Continue an existing conversation; omit to start a new one.
        """
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
        """
        Send a message to an agent and stream the reply token by token.

        Args:
            agent_id:  Agent ID or slug.
            message:   The message to send.
            model:     Model to run this message with (required). One of the
                       supported model IDs, e.g. ``"claude-sonnet-4.6"`` or ``"gpt-5.5"``.
            thread_id: Continue an existing conversation; omit to start a new one.
        """
        return chat_stream_session(
            self._http,
            "agents",
            agent_id,
            message,
            model=model,
            thread_id=thread_id,
        )

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> Page[Agent]:
        """
        List agents in the organisation.

        Args:
            page_size:  Items per page (default 25).
            page_token: Opaque token from a previous page's ``next_page_token``.
        """
        validate_page_size(page_size)
        return self._list_page(page_size, page_token)

    def _list_page(self, page_size: int, page_token: Optional[str]) -> Page[Agent]:
        params = aip_list_params(page_size, page_token)
        data = with_retry(
            lambda: self._http.get("/api/v1/agents", params=params),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "agents",
            _map_agent,
            lambda cur: self._list_page(page_size, cur),
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

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> AsyncPage[Agent]:
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token)

    async def _list_page(
        self, page_size: int, page_token: Optional[str]
    ) -> AsyncPage[Agent]:
        params = aip_list_params(page_size, page_token)
        data = await async_with_retry(
            lambda: self._http.get("/api/v1/agents", params=params),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "agents",
            _map_agent,
            lambda cur: self._list_page(page_size, cur),
        )

    async def get(self, agent_id: Union[int, str]) -> Agent:
        validate_id(agent_id, name="agent_id")
        safe_id = quote(str(agent_id), safe="")
        data = await async_with_retry(
            lambda: self._http.get(f"/api/v1/agents/{safe_id}"),
            self._config.max_retries,
        )
        return _translate_agent(_AgentWire.model_validate(data))
