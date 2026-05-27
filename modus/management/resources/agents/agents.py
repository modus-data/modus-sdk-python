"""Agents resource — /api/v1/agents (full CRUD, management SDK)"""

from __future__ import annotations
from typing import Any, Dict, Optional, Union
from urllib.parse import quote

from modus._config import ModusConfig
from modus._exceptions import ModusError
from modus._http import AsyncHttpClient, HttpClient
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id, validate_limit
from ..._wire.agents import _AgentWire
from ...types.agents import Agent
from modus.types.pagination import AsyncPage, Page
from ._translate import _translate_agent
from ._update_body import _AgentCreateBody, _AgentUpdateBody


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

    def list(self, *, limit: int = 20, cursor: Optional[str] = None) -> Page[Agent]:
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
            raise ModusError("Unexpected list response: missing 'items'")
        items = [_translate_agent(_AgentWire.model_validate(r)) for r in data.get("items", [])]
        next_cursor = data.get("nextCursor") or None
        return Page(items=items, next_cursor=next_cursor,
                    _fetch_page=lambda cur: self._list_page(limit, cur))

    def get(self, agent_id: Union[int, str]) -> Agent:
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
        validate_id(agent_id, name="agent_id")
        safe_id = quote(str(agent_id), safe="")
        raw = with_retry(
            lambda: self._http.post(f"/api/v1/agents/{safe_id}/deploy"),
            self._config.max_retries,
        )
        agent_data = raw.get("agent", raw) if isinstance(raw, dict) else raw
        return _translate_agent(_AgentWire.model_validate(agent_data))

    def delete(self, agent_id: Union[int, str]) -> None:
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
            raise ModusError("Unexpected list response: missing 'items'")
        items = [_translate_agent(_AgentWire.model_validate(r)) for r in data.get("items", [])]
        next_cursor = data.get("nextCursor") or None
        return AsyncPage(items=items, next_cursor=next_cursor,
                         _fetch_page=lambda cur: self._list_page(limit, cur))

    async def get(self, agent_id: Union[int, str]) -> Agent:
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
