"""Create, update, and deploy agents via the management client."""

from __future__ import annotations

from typing import List, Optional, Union

from modus._config import ModusConfig
from modus._generated.models import (
    AgentDeployResponseDto,
    AgentDto,
    TransferOwnershipDto,
)
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._pagination import aip_list_params, build_aip_page_mapped, build_async_aip_page_mapped
from modus._query import update_mask_query
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id, validate_page_size
from modus.types.agents import Agent, AgentType
from modus.types.pagination import AsyncPage, Page
from modus.types.views import VariationView

from ...types.agent_selection import AgentSelectionInput, dump_agent_selection
from ...types.triggers import TriggerInput, dump_trigger
from ...types.workflow import WorkflowGraphInput, dump_workflow_structure
from .._access_config_write import (
    access_config_body_for_create,
    access_config_body_for_update,
)
from ._update_body import _AgentCreateBody, _AgentUpdateBody


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
        view: Optional[VariationView] = None,
        include_variation: Optional[bool] = None,
    ) -> Page[Agent]:
        """
        List all Modus agents in the organisation.

        Args:
            page_size:         Maximum number of items to return (default 25).
            page_token:        Token from a previous page's ``next_page_token``; omit for the first page.
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
        """Retrieve a Modus agent with full configuration."""
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
            lambda: invoke_operation(
                self._http, "AgentsController_create", json_body=body
            ),
            self._config.max_retries,
        )
        return _parse_agent(raw)

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
        access_config = access_config_body_for_update(
            guardrails,
            lambda: with_retry(
                lambda: invoke_operation(
                    self._http,
                    "AgentsController_get",
                    path_params={"id": agent_id},
                ),
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
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "AgentsController_update",
                path_params={"id": agent_id},
                query=update_mask_query(update_mask),
                json_body=body,
            ),
            self._config.max_retries,
        )
        return _parse_agent(raw)

    def deploy(self, agent_id: Union[int, str]) -> Agent:
        """Publish the current draft of a Modus agent."""
        validate_id(agent_id, name="agent_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "AgentsController_deploy",
                path_params={"id": agent_id},
                json_body={},
            ),
            self._config.max_retries,
        )
        return AgentDeployResponseDto.model_validate(raw).agent

    def delete(self, agent_id: Union[int, str]) -> None:
        """Delete a Modus agent."""
        validate_id(agent_id, name="agent_id")
        with_retry(
            lambda: invoke_operation(
                self._http,
                "AgentsController_delete",
                path_params={"id": agent_id},
            ),
            self._config.max_retries,
        )

    def request_ownership_transfer(
        self, agent_id: Union[int, str], *, new_owner_user_id: str,
    ) -> Agent:
        """Start transferring ownership of an agent to another organisation member."""
        validate_id(agent_id, name="agent_id")
        body = TransferOwnershipDto(new_owner_user_id=new_owner_user_id)
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "AgentsController_requestOwnershipTransfer",
                path_params={"id": agent_id},
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return _parse_agent(raw)

    def cancel_ownership_transfer(self, agent_id: Union[int, str]) -> Agent:
        """Cancel a pending agent ownership transfer."""
        validate_id(agent_id, name="agent_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "AgentsController_cancelOwnershipTransfer",
                path_params={"id": agent_id},
            ),
            self._config.max_retries,
        )
        return _parse_agent(raw)

    def accept_ownership_transfer(self, agent_id: Union[int, str]) -> Agent:
        """Accept a pending agent ownership transfer."""
        validate_id(agent_id, name="agent_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "AgentsController_acceptOwnershipTransfer",
                path_params={"id": agent_id},
                json_body={},
            ),
            self._config.max_retries,
        )
        return _parse_agent(raw)

    def restore(self, agent_id: Union[int, str]) -> Agent:
        """Restore a deleted agent."""
        validate_id(agent_id, name="agent_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "AgentsController_restore",
                path_params={"id": agent_id},
                json_body={},
            ),
            self._config.max_retries,
        )
        return _parse_agent(raw)


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
        view: Optional[VariationView] = None,
        include_variation: Optional[bool] = None,
    ) -> AsyncPage[Agent]:
        """
        List all Modus agents in the organisation.

        Args:
            page_size:         Maximum number of items to return (default 25).
            page_token:        Token from a previous page's ``next_page_token``; omit for the first page.
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
        """Retrieve a Modus agent with full configuration."""
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
            lambda: invoke_operation_async(
                self._http, "AgentsController_create", json_body=body
            ),
            self._config.max_retries,
        )
        return _parse_agent(raw)

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
        if guardrails is not None:
            existing = await async_with_retry(
                lambda: invoke_operation_async(
                    self._http,
                    "AgentsController_get",
                    path_params={"id": agent_id},
                ),
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
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "AgentsController_update",
                path_params={"id": agent_id},
                query=update_mask_query(update_mask),
                json_body=body,
            ),
            self._config.max_retries,
        )
        return _parse_agent(raw)

    async def deploy(self, agent_id: Union[int, str]) -> Agent:
        validate_id(agent_id, name="agent_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "AgentsController_deploy",
                path_params={"id": agent_id},
                json_body={},
            ),
            self._config.max_retries,
        )
        return AgentDeployResponseDto.model_validate(raw).agent

    async def delete(self, agent_id: Union[int, str]) -> None:
        validate_id(agent_id, name="agent_id")
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "AgentsController_delete",
                path_params={"id": agent_id},
            ),
            self._config.max_retries,
        )

    async def request_ownership_transfer(
        self, agent_id: Union[int, str], *, new_owner_user_id: str,
    ) -> Agent:
        """Start transferring ownership of an agent to another organisation member."""
        validate_id(agent_id, name="agent_id")
        body = TransferOwnershipDto(new_owner_user_id=new_owner_user_id)
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "AgentsController_requestOwnershipTransfer",
                path_params={"id": agent_id},
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return _parse_agent(raw)

    async def cancel_ownership_transfer(self, agent_id: Union[int, str]) -> Agent:
        """Cancel a pending agent ownership transfer."""
        validate_id(agent_id, name="agent_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "AgentsController_cancelOwnershipTransfer",
                path_params={"id": agent_id},
            ),
            self._config.max_retries,
        )
        return _parse_agent(raw)

    async def accept_ownership_transfer(self, agent_id: Union[int, str]) -> Agent:
        """Accept a pending agent ownership transfer."""
        validate_id(agent_id, name="agent_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "AgentsController_acceptOwnershipTransfer",
                path_params={"id": agent_id},
                json_body={},
            ),
            self._config.max_retries,
        )
        return _parse_agent(raw)

    async def restore(self, agent_id: Union[int, str]) -> Agent:
        """Restore a deleted agent."""
        validate_id(agent_id, name="agent_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "AgentsController_restore",
                path_params={"id": agent_id},
                json_body={},
            ),
            self._config.max_retries,
        )
        return _parse_agent(raw)
