"""Agents resource — /api/v1/agents (full CRUD, management SDK)"""

from __future__ import annotations

from typing import List, Optional, Union
from urllib.parse import quote

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._pagination import aip_list_params, build_aip_page_mapped, build_async_aip_page_mapped
from modus._query import with_update_mask as _with_update_mask
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id, validate_page_size
from modus.types.pagination import AsyncPage, Page

from ..._wire.agents import _AgentWire
from ...types.agent_selection import AgentSelectionInput, dump_agent_selection
from ...types.agents import Agent, AgentType
from ...types.triggers import TriggerInput, dump_trigger
from ...types.workflow import WorkflowGraphInput, dump_workflow_structure
from .._access_config_write import (
    access_config_body_for_create,
    access_config_body_for_update,
)
from ._translate import _translate_agent
from ._update_body import _AgentCreateBody, _AgentUpdateBody


def _map_agent(raw: dict) -> Agent:
    return _translate_agent(_AgentWire.model_validate(raw))


def _agents_list_params(
    page_size: int,
    page_token: Optional[str],
    search: Optional[str],
    type: Optional[AgentType],
) -> dict:
    extra: dict = {}
    if search is not None:
        extra["search"] = search
    if type is not None:
        extra["type"] = type
    return aip_list_params(page_size, page_token, **extra)


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
        search: Optional[str] = None,
        type: Optional[AgentType] = None,
    ) -> Page[Agent]:
        """
        List all Modus agents in the organisation.

        Args:
            page_size:  Maximum number of items to return (default 25).
            page_token: Token from a previous page's ``next_page_token``; omit for the first page.
            search:     Case-insensitive substring filter on the agent name.
            type:       Filter by agent type: ``"task"`` or ``"workflow"``.
        """
        validate_page_size(page_size)
        return self._list_page(page_size, page_token, search, type)

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        search: Optional[str] = None,
        type: Optional[AgentType] = None,
    ) -> Page[Agent]:
        params = _agents_list_params(page_size, page_token, search, type)
        data = with_retry(
            lambda: self._http.get("/api/v1/agents", params=params),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "agents",
            _map_agent,
            lambda cur: self._list_page(page_size, cur, search, type),
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
        type: AgentType,
        *,
        description: Optional[str] = None,
        trigger: Optional[TriggerInput] = None,
        agent_selection: Optional[AgentSelectionInput] = None,
        workflow_structure: Optional[WorkflowGraphInput] = None,
        guardrails: Optional[List[str]] = None,
    ) -> Agent:
        """Create a new Modus agent.

        Args:
            name: Display name for the agent.
            type: ``"task"`` for single-step skill orchestration, or ``"workflow"``
                  for a multi-step graph.
            guardrails: Runtime guardrail labels (for example ``\"no-pii\"``).
                When set, the agent is created with these labels under the
                organisation default sharing rules. Omit (``None``) to create
                with no guardrails. ACL fields cannot be set from the SDK.
        """
        body = _AgentCreateBody(
            name=name, type=type, description=description,
            trigger=dump_trigger(trigger),
            agent_selection=dump_agent_selection(agent_selection),
            workflow_structure=dump_workflow_structure(workflow_structure),
            access_config=access_config_body_for_create(guardrails),
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
        type: Optional[AgentType] = None,
        description: Optional[str] = None,
        trigger: Optional[TriggerInput] = None,
        agent_selection: Optional[AgentSelectionInput] = None,
        workflow_structure: Optional[WorkflowGraphInput] = None,
        guardrails: Optional[List[str]] = None,
        update_mask: Optional[str] = None,
    ) -> Agent:
        """Update a Modus agent's configuration.

        Only the fields you pass are changed. To clear a field, name it in
        ``update_mask`` (a comma-separated list of field names) and leave its
        argument unset — the server sets each masked field to null and leaves
        fields not named in the mask untouched.

        Args:
            guardrails: Runtime guardrail labels to set on the agent. Fetches
                the current agent first and merges these labels into its access
                configuration (an extra ``get`` request). Omit (``None``) to
                leave guardrails unchanged. Pass ``[]`` to clear all guardrails.
        """
        validate_id(agent_id, name="agent_id")
        safe_id = quote(str(agent_id), safe="")
        access_config = access_config_body_for_update(
            guardrails,
            lambda: with_retry(
                lambda: self._http.get(f"/api/v1/agents/{safe_id}"),
                self._config.max_retries,
            ),
        )
        body = _AgentUpdateBody(
            name=name, type=type, description=description,
            trigger=dump_trigger(trigger),
            agent_selection=dump_agent_selection(agent_selection),
            workflow_structure=dump_workflow_structure(workflow_structure),
            access_config=access_config,
        ).model_dump(by_alias=True, exclude_none=update_mask is None)
        path = _with_update_mask(f"/api/v1/agents/{safe_id}", update_mask)
        raw = with_retry(
            lambda: self._http.patch(path, json=body),
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
        search: Optional[str] = None,
        type: Optional[AgentType] = None,
    ) -> AsyncPage[Agent]:
        """
        List all Modus agents in the organisation.

        Args:
            page_size:  Maximum number of items to return (default 25).
            page_token: Token from a previous page's ``next_page_token``; omit for the first page.
            search:     Case-insensitive substring filter on the agent name.
            type:       Filter by agent type: ``"task"`` or ``"workflow"``.
        """
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token, search, type)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        search: Optional[str] = None,
        type: Optional[AgentType] = None,
    ) -> AsyncPage[Agent]:
        params = _agents_list_params(page_size, page_token, search, type)
        data = await async_with_retry(
            lambda: self._http.get("/api/v1/agents", params=params),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "agents",
            _map_agent,
            lambda cur: self._list_page(page_size, cur, search, type),
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

    async def create(self, name: str, type: AgentType, *,
                     description: Optional[str] = None,
                     trigger: Optional[TriggerInput] = None,
                     agent_selection: Optional[AgentSelectionInput] = None,
                     workflow_structure: Optional[WorkflowGraphInput] = None,
                     guardrails: Optional[List[str]] = None) -> Agent:
        """Create a new Modus agent.

        Args:
            name: Display name for the agent.
            type: ``"task"`` for single-step skill orchestration, or ``"workflow"``
                  for a multi-step graph.
            guardrails: Runtime guardrail labels (for example ``\"no-pii\"``).
                When set, the agent is created with these labels under the
                organisation default sharing rules. Omit (``None``) to create
                with no guardrails. ACL fields cannot be set from the SDK.
        """
        body = _AgentCreateBody(
            name=name, type=type, description=description,
            trigger=dump_trigger(trigger),
            agent_selection=dump_agent_selection(agent_selection),
            workflow_structure=dump_workflow_structure(workflow_structure),
            access_config=access_config_body_for_create(guardrails),
        ).model_dump(by_alias=True, exclude_none=True)
        raw = await async_with_retry(
            lambda: self._http.post("/api/v1/agents", json=body),
            self._config.max_retries,
        )
        return _translate_agent(_AgentWire.model_validate(raw))

    async def update(self, agent_id: Union[int, str], *,
                     name: Optional[str] = None, type: Optional[AgentType] = None,
                     description: Optional[str] = None,
                     trigger: Optional[TriggerInput] = None,
                     agent_selection: Optional[AgentSelectionInput] = None,
                     workflow_structure: Optional[WorkflowGraphInput] = None,
                     guardrails: Optional[List[str]] = None,
                     update_mask: Optional[str] = None) -> Agent:
        """Update a Modus agent's configuration.

        Only the fields you pass are changed. To clear a field, name it in
        ``update_mask`` (a comma-separated list of field names) and leave its
        argument unset — the server sets each masked field to null and leaves
        fields not named in the mask untouched.

        Args:
            guardrails: Runtime guardrail labels to set on the agent. Fetches
                the current agent first and merges these labels into its access
                configuration (an extra ``get`` request). Omit (``None``) to
                leave guardrails unchanged. Pass ``[]`` to clear all guardrails.
        """
        validate_id(agent_id, name="agent_id")
        safe_id = quote(str(agent_id), safe="")
        if guardrails is not None:
            existing = await async_with_retry(
                lambda: self._http.get(f"/api/v1/agents/{safe_id}"),
                self._config.max_retries,
            )
            access_config = access_config_body_for_update(guardrails, lambda: existing)
        else:
            access_config = None
        body = _AgentUpdateBody(
            name=name, type=type, description=description,
            trigger=dump_trigger(trigger),
            agent_selection=dump_agent_selection(agent_selection),
            workflow_structure=dump_workflow_structure(workflow_structure),
            access_config=access_config,
        ).model_dump(by_alias=True, exclude_none=update_mask is None)
        path = _with_update_mask(f"/api/v1/agents/{safe_id}", update_mask)
        raw = await async_with_retry(
            lambda: self._http.patch(path, json=body),
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
