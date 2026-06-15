"""Read-only agents resource for the consumption client."""

from __future__ import annotations

from typing import Optional, Union

from ..._config import ModusConfig
from ..._generated.models import AgentDto
from ..._http import AsyncHttpClient, HttpClient
from ..._openapi_invoke import invoke_operation, invoke_operation_async
from ..._pagination import (
    aip_list_params,
    build_aip_page_mapped,
    build_async_aip_page_mapped,
)
from ..._retry import async_with_retry, with_retry
from ..._validation import validate_id, validate_page_size
from ...types.agents import Agent, AgentType
from ...types.pagination import AsyncPage, Page
from ...types.views import VariationView
from .runs import AgentRunsResource, AsyncAgentRunsResource


def _parse_agent(raw: dict) -> Agent:
    return AgentDto.model_validate(raw)


def _agents_list_params(
    page_size: int,
    page_token: Optional[str],
    search: Optional[str],
    type: Optional[AgentType],
    view: Optional[VariationView],
    include_variation: Optional[bool],
) -> dict:
    extra: dict = {}
    if search is not None:
        extra["search"] = search
    if type is not None:
        extra["type"] = type
    if view is not None:
        extra["view"] = view
    if include_variation is not None:
        extra["includeVariation"] = include_variation
    return aip_list_params(page_size, page_token, **extra)


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

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        search: Optional[str] = None,
        type: Optional[AgentType] = None,
        view: Optional[VariationView] = None,
        include_variation: Optional[bool] = None,
    ) -> Page[Agent]:
        """
        List agents in the organisation.

        Args:
            page_size:         Items per page (default 25).
            page_token:        Opaque token from a previous page's ``next_page_token``.
            search:            Case-insensitive substring filter on the agent name.
            type:              Filter by agent type: ``"task"`` or ``"workflow"``.
            view:              Variation view — ``"active"`` (deployed) or ``"draft"``.
            include_variation: Include variation payload on each list row.
        """
        validate_page_size(page_size)
        return self._list_page(
            page_size, page_token, search, type, view, include_variation
        )

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        search: Optional[str] = None,
        type: Optional[AgentType] = None,
        view: Optional[VariationView] = None,
        include_variation: Optional[bool] = None,
    ) -> Page[Agent]:
        params = _agents_list_params(
            page_size, page_token, search, type, view, include_variation
        )
        data = with_retry(
            lambda: invoke_operation(
                self._http, "AgentsController_list", query=params
            ),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "agents",
            _parse_agent,
            lambda cur: self._list_page(
                page_size, cur, search, type, view, include_variation
            ),
        )

    def get(
        self,
        agent_id: Union[int, str],
        *,
        view: Optional[VariationView] = None,
    ) -> Agent:
        """
        Retrieve an agent by ID or slug.

        Args:
            view: Variation view — ``"active"`` (deployed) or ``"draft"``.

        Raises:
            NotFoundError: if no agent with this ID/slug exists.
        """
        validate_id(agent_id, name="agent_id")
        query = {} if view is None else {"view": view}
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "AgentsController_get",
                path_params={"id": agent_id},
                query=query or None,
            ),
            self._config.max_retries,
        )
        return _parse_agent(data)


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

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        search: Optional[str] = None,
        type: Optional[AgentType] = None,
        view: Optional[VariationView] = None,
        include_variation: Optional[bool] = None,
    ) -> AsyncPage[Agent]:
        """
        List agents in the organisation.

        Args:
            page_size:         Items per page (default 25).
            page_token:        Opaque token from a previous page's ``next_page_token``.
            search:            Case-insensitive substring filter on the agent name.
            type:              Filter by agent type: ``"task"`` or ``"workflow"``.
            view:              Variation view — ``"active"`` (deployed) or ``"draft"``.
            include_variation: Include variation payload on each list row.
        """
        validate_page_size(page_size)
        return await self._list_page(
            page_size, page_token, search, type, view, include_variation
        )

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        search: Optional[str] = None,
        type: Optional[AgentType] = None,
        view: Optional[VariationView] = None,
        include_variation: Optional[bool] = None,
    ) -> AsyncPage[Agent]:
        params = _agents_list_params(
            page_size, page_token, search, type, view, include_variation
        )
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, "AgentsController_list", query=params
            ),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "agents",
            _parse_agent,
            lambda cur: self._list_page(
                page_size, cur, search, type, view, include_variation
            ),
        )

    async def get(
        self,
        agent_id: Union[int, str],
        *,
        view: Optional[VariationView] = None,
    ) -> Agent:
        validate_id(agent_id, name="agent_id")
        query = {} if view is None else {"view": view}
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "AgentsController_get",
                path_params={"id": agent_id},
                query=query or None,
            ),
            self._config.max_retries,
        )
        return _parse_agent(data)
