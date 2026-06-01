"""Agents resource — /api/v1/agents (full CRUD, management SDK)"""

from __future__ import annotations
from typing import Any, Dict, Optional, Union
from urllib.parse import quote

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._retry import async_with_retry, with_retry
from modus._pagination import aip_list_params, build_aip_page_mapped, build_async_aip_page_mapped
from modus._validation import validate_id, validate_page_size
from ..._wire.agents import _AgentWire
from ...types.agents import Agent
from modus.types.pagination import AsyncPage, Page
from ._translate import _translate_agent
from ._update_body import _AgentCreateBody, _AgentUpdateBody


def _map_agent(raw: dict) -> Agent:
    return _translate_agent(_AgentWire.model_validate(raw))


class AgentsResource:
    """
    Full CRUD access to Modus agents.

    mgmt.agents.list()               → Page[Agent]
    mgmt.agents.get(agent_id)        → Agent (with variation fields)
    mgmt.agents.create(name, type)   → Agent
    mgmt.agents.update(agent_id, ..) → Agent
    mgmt.agents.deploy(agent_id)     → Agent
    mgmt.agents.delete(agent_id)     → None
    """

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> Page[Agent]:
        """
        List all Modus agents in the organisation.

        Args:
            page_size:  Maximum number of items to return (default 25).
            page_token: Token from a previous page's ``next_page_token``; omit for the first page.
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
        """Retrieve a Modus agent with full configuration."""
        validate_id(agent_id, name="agent_id")
        safe_id = quote(str(agent_id), safe="")
        data = with_retry(
            lambda: self._http.get(f"/api/v1/agents/{safe_id}"),
            self._config.max_retries,
        )
        return _translate_agent(_AgentWire.model_validate(data))

    def create(
        self,
        name: str,
        type: str,  # "task" | "workflow"
        *,
        description: Optional[str] = None,
        trigger: Optional[Dict[str, Any]] = None,
        agent_selection: Optional[Dict[str, Any]] = None,
        workflow_structure: Optional[Dict[str, Any]] = None,
        access_config: Optional[Dict[str, Any]] = None,
    ) -> Agent:
        """Create a new Modus agent in the organisation."""
        body = _AgentCreateBody(
            name=name, type=type, description=description,
            trigger=trigger, agent_selection=agent_selection,
            workflow_structure=workflow_structure, access_config=access_config,
        ).model_dump(by_alias=True, exclude_none=True)
        raw = with_retry(
            lambda: self._http.post("/api/v1/agents", json=body),
            self._config.max_retries,
        )
        return _translate_agent(_AgentWire.model_validate(raw))

    def update(
        self,
        agent_id: Union[int, str],
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        trigger: Optional[Dict[str, Any]] = None,
        agent_selection: Optional[Dict[str, Any]] = None,
        workflow_structure: Optional[Dict[str, Any]] = None,
        access_config: Optional[Dict[str, Any]] = None,
    ) -> Agent:
        """Update a Modus agent's configuration."""
        body = _AgentUpdateBody(
            name=name, description=description, trigger=trigger,
            agent_selection=agent_selection, workflow_structure=workflow_structure,
            access_config=access_config,
        ).model_dump(by_alias=True, exclude_none=True)
        validate_id(agent_id, name="agent_id")
        safe_id = quote(str(agent_id), safe="")
        raw = with_retry(
            lambda: self._http.patch(f"/api/v1/agents/{safe_id}", json=body),
            self._config.max_retries,
        )
        return _translate_agent(_AgentWire.model_validate(raw))

    def deploy(self, agent_id: Union[int, str]) -> Agent:
        """Publish the current draft of a Modus agent."""
        validate_id(agent_id, name="agent_id")
        safe_id = quote(str(agent_id), safe="")
        raw = with_retry(
            lambda: self._http.post(f"/api/v1/agents/{safe_id}/deploy"),
            self._config.max_retries,
        )
        agent_data = raw.get("agent", raw) if isinstance(raw, dict) else raw
        return _translate_agent(_AgentWire.model_validate(agent_data))

    def delete(self, agent_id: Union[int, str]) -> None:
        """Delete a Modus agent."""
        validate_id(agent_id, name="agent_id")
        safe_id = quote(str(agent_id), safe="")
        with_retry(
            lambda: self._http.delete(f"/api/v1/agents/{safe_id}"),
            self._config.max_retries,
        )


class AsyncAgentsResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> AsyncPage[Agent]:
        """
        List all Modus agents in the organisation.

        Args:
            page_size:  Maximum number of items to return (default 25).
            page_token: Token from a previous page's ``next_page_token``; omit for the first page.
        """
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
        """Retrieve a Modus agent with full configuration."""
        validate_id(agent_id, name="agent_id")
        safe_id = quote(str(agent_id), safe="")
        data = await async_with_retry(
            lambda: self._http.get(f"/api/v1/agents/{safe_id}"),
            self._config.max_retries,
        )
        return _translate_agent(_AgentWire.model_validate(data))

    async def create(self, name: str, type: str, *,
                     description: Optional[str] = None,
                     trigger: Optional[Dict[str, Any]] = None,
                     agent_selection: Optional[Dict[str, Any]] = None,
                     workflow_structure: Optional[Dict[str, Any]] = None,
                     access_config: Optional[Dict[str, Any]] = None) -> Agent:
        body = _AgentCreateBody(
            name=name, type=type, description=description, trigger=trigger,
            agent_selection=agent_selection, workflow_structure=workflow_structure,
            access_config=access_config,
        ).model_dump(by_alias=True, exclude_none=True)
        raw = await async_with_retry(
            lambda: self._http.post("/api/v1/agents", json=body),
            self._config.max_retries,
        )
        return _translate_agent(_AgentWire.model_validate(raw))

    async def update(self, agent_id: Union[int, str], *,
                     name: Optional[str] = None, description: Optional[str] = None,
                     trigger: Optional[Dict[str, Any]] = None,
                     agent_selection: Optional[Dict[str, Any]] = None,
                     workflow_structure: Optional[Dict[str, Any]] = None,
                     access_config: Optional[Dict[str, Any]] = None) -> Agent:
        body = _AgentUpdateBody(
            name=name, description=description, trigger=trigger,
            agent_selection=agent_selection, workflow_structure=workflow_structure,
            access_config=access_config,
        ).model_dump(by_alias=True, exclude_none=True)
        validate_id(agent_id, name="agent_id")
        safe_id = quote(str(agent_id), safe="")
        raw = await async_with_retry(
            lambda: self._http.patch(f"/api/v1/agents/{safe_id}", json=body),
            self._config.max_retries,
        )
        return _translate_agent(_AgentWire.model_validate(raw))

    async def deploy(self, agent_id: Union[int, str]) -> Agent:
        validate_id(agent_id, name="agent_id")
        safe_id = quote(str(agent_id), safe="")
        raw = await async_with_retry(
            lambda: self._http.post(f"/api/v1/agents/{safe_id}/deploy"),
            self._config.max_retries,
        )
        agent_data = raw.get("agent", raw) if isinstance(raw, dict) else raw
        return _translate_agent(_AgentWire.model_validate(agent_data))

    async def delete(self, agent_id: Union[int, str]) -> None:
        validate_id(agent_id, name="agent_id")
        safe_id = quote(str(agent_id), safe="")
        await async_with_retry(
            lambda: self._http.delete(f"/api/v1/agents/{safe_id}"),
            self._config.max_retries,
        )
