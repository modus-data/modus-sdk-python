"""Create, update, and deploy workflows via the management client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Union

from modus._config import ModusConfig
from modus._generated.models import (
    AgentDeployResponseDto,
    TransferOwnershipDto,
    WorkflowDto,
)
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._pagination import (
    aip_list_params,
    build_aip_page_mapped,
    build_async_aip_page_mapped,
)
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
from ._update_body import _WorkflowCreateBody, _WorkflowUpdateBody
from .interfaces import AsyncWorkflowInterfacesResource, WorkflowInterfacesResource


@dataclass(frozen=True)
class ManagementWorkflowsOperations:
    """Which operationIds a management workflows-shaped resource calls."""

    list: str
    get: str
    create: str
    update: str
    deploy: str
    delete: str
    restore: str
    request_ownership_transfer: str
    cancel_ownership_transfer: str
    accept_ownership_transfer: str
    toggle: str


MANAGEMENT_WORKFLOW_OPERATIONS = ManagementWorkflowsOperations(
    list="WorkflowsController_list",
    get="WorkflowsController_get",
    create="WorkflowsController_create",
    update="WorkflowsController_update",
    deploy="WorkflowsController_deploy",
    delete="WorkflowsController_delete",
    restore="WorkflowsController_restore",
    request_ownership_transfer="WorkflowsController_requestOwnershipTransfer",
    cancel_ownership_transfer="WorkflowsController_cancelOwnershipTransfer",
    accept_ownership_transfer="WorkflowsController_acceptOwnershipTransfer",
    toggle="WorkflowsController_toggle",
)


def _parse_workflow(raw: dict) -> Agent:
    return WorkflowDto.model_validate(raw)


def _parse_deploy_workflow(raw: Any) -> Agent:
    """Validate deploy envelope; return the published workflow."""
    return AgentDeployResponseDto.model_validate(raw).workflow


def _workflows_list_params(
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


class WorkflowsResource:
    """
    Full CRUD access to Modus workflows.

    mgmt.workflows.list()                  → Page[Agent]
    mgmt.workflows.get(workflow_id)        → Agent (with variation fields)
    mgmt.workflows.create(name, type)      → Agent
    mgmt.workflows.update(workflow_id, ..) → Agent
    mgmt.workflows.deploy(workflow_id)     → Agent
    mgmt.workflows.delete(workflow_id)     → None
    """

    def __init__(
        self,
        http: HttpClient,
        config: ModusConfig,
        ops: "ManagementWorkflowsOperations" = MANAGEMENT_WORKFLOW_OPERATIONS,
    ) -> None:
        self._http = http
        self._config = config
        self._ops = ops

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
        List all Modus workflows in the organisation.

        Args:
            page_size:         Maximum number of items to return (default 25).
            page_token:        Token from a previous page's ``next_page_token``; omit for the first page.
            search:            Case-insensitive substring filter on the workflow name.
            type:              Filter by workflow type: ``"task"`` or ``"workflow"``.
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
        params = _workflows_list_params(
            page_size, page_token, search, type, view, include_variation
        )
        data = with_retry(
            lambda: invoke_operation(
                self._http, self._ops.list, query=params
            ),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "workflows",
            _parse_workflow,
            lambda cur: self._list_page(
                page_size, cur, search, type, view, include_variation
            ),
        )

    def get(
        self,
        workflow_id: Union[int, str],
        *,
        view: Optional[VariationView] = None,
    ) -> Agent:
        """Retrieve a Modus workflow with full configuration."""
        validate_id(workflow_id, name="workflow_id")
        query = {} if view is None else {"view": view}
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.get,
                path_params={"id": workflow_id},
                query=query or None,
            ),
            self._config.max_retries,
        )
        return _parse_workflow(data)

    def interfaces(self, workflow_id: Union[int, str]) -> WorkflowInterfacesResource:
        """Return the interfaces sub-resource scoped to ``workflow_id``."""
        return WorkflowInterfacesResource(self._http, self._config, workflow_id)

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
        """Create a new Modus workflow.

        Args:
            name: Display name for the workflow.
            type: ``"task"`` for single-step skill orchestration, or ``"workflow"``
                  for a multi-step graph.
            guardrails: Runtime guardrail labels (for example ``\"no-pii\"``).
                When set, the workflow is created with these labels under the
                organisation default sharing rules. Omit (``None``) to create
                with no guardrails. ACL fields cannot be set from the SDK.
        """
        body = _WorkflowCreateBody(
            name=name, type=type, description=description,
            trigger=dump_trigger(trigger),
            agent_selection=dump_agent_selection(agent_selection),
            workflow_structure=dump_workflow_structure(workflow_structure),
            access_config=access_config_body_for_create(guardrails),
        ).model_dump(by_alias=True, exclude_none=True)
        raw = with_retry(
            lambda: invoke_operation(
                self._http, self._ops.create, json_body=body
            ),
            self._config.max_retries,
        )
        return _parse_workflow(raw)

    def update(
        self,
        workflow_id: Union[int, str],
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
        """Update a Modus workflow's configuration.

        Only the fields you pass are changed. To clear a field, name it in
        ``update_mask`` (a comma-separated list of field names) and leave its
        argument unset — the server sets each masked field to null and leaves
        fields not named in the mask untouched.

        Args:
            guardrails: Runtime guardrail labels to set on the workflow. Fetches
                the current workflow first and merges these labels into its access
                configuration (an extra ``get`` request). Omit (``None``) to
                leave guardrails unchanged. Pass ``[]`` to clear all guardrails.
        """
        validate_id(workflow_id, name="workflow_id")
        access_config = access_config_body_for_update(
            guardrails,
            lambda: with_retry(
                lambda: invoke_operation(
                    self._http,
                    self._ops.get,
                    path_params={"id": workflow_id},
                ),
                self._config.max_retries,
            ),
        )
        body = _WorkflowUpdateBody(
            name=name, type=type, description=description,
            trigger=dump_trigger(trigger),
            agent_selection=dump_agent_selection(agent_selection),
            workflow_structure=dump_workflow_structure(workflow_structure),
            access_config=access_config,
        ).model_dump(by_alias=True, exclude_none=update_mask is None)
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.update,
                path_params={"id": workflow_id},
                query=update_mask_query(update_mask),
                json_body=body,
            ),
            self._config.max_retries,
        )
        return _parse_workflow(raw)

    def deploy(self, workflow_id: Union[int, str]) -> Agent:
        """Publish the current draft of a Modus workflow."""
        validate_id(workflow_id, name="workflow_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.deploy,
                path_params={"id": workflow_id},
                json_body={},
            ),
            self._config.max_retries,
            retry_not_found_on_deploy=True,
        )
        return _parse_deploy_workflow(raw)

    def toggle(self, workflow_id: Union[int, str], *, active: bool) -> Agent:
        """Enable or disable a workflow."""
        validate_id(workflow_id, name="workflow_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http, self._ops.toggle, path_params={"id": workflow_id},
                json_body={"active": active},
            ),
            self._config.max_retries,
        )
        return _parse_workflow(raw)

    def delete(self, workflow_id: Union[int, str]) -> None:
        """Delete a Modus workflow."""
        validate_id(workflow_id, name="workflow_id")
        with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.delete,
                path_params={"id": workflow_id},
            ),
            self._config.max_retries,
        )

    def request_ownership_transfer(
        self, workflow_id: Union[int, str], *, new_owner_user_id: str,
    ) -> Agent:
        """Start transferring ownership of a workflow to another organisation member."""
        validate_id(workflow_id, name="workflow_id")
        body = TransferOwnershipDto(new_owner_user_id=new_owner_user_id)
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.request_ownership_transfer,
                path_params={"id": workflow_id},
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return _parse_workflow(raw)

    def cancel_ownership_transfer(self, workflow_id: Union[int, str]) -> Agent:
        """Cancel a pending workflow ownership transfer."""
        validate_id(workflow_id, name="workflow_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.cancel_ownership_transfer,
                path_params={"id": workflow_id},
            ),
            self._config.max_retries,
        )
        return _parse_workflow(raw)

    def accept_ownership_transfer(self, workflow_id: Union[int, str]) -> Agent:
        """Accept a pending workflow ownership transfer."""
        validate_id(workflow_id, name="workflow_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.accept_ownership_transfer,
                path_params={"id": workflow_id},
                json_body={},
            ),
            self._config.max_retries,
        )
        return _parse_workflow(raw)

    def restore(self, workflow_id: Union[int, str]) -> Agent:
        """Restore a deleted workflow."""
        validate_id(workflow_id, name="workflow_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.restore,
                path_params={"id": workflow_id},
                json_body={},
            ),
            self._config.max_retries,
        )
        return _parse_workflow(raw)


class AsyncWorkflowsResource:
    def __init__(
        self,
        http: AsyncHttpClient,
        config: ModusConfig,
        ops: "ManagementWorkflowsOperations" = MANAGEMENT_WORKFLOW_OPERATIONS,
    ) -> None:
        self._http = http
        self._config = config
        self._ops = ops

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
        List all Modus workflows in the organisation.

        Args:
            page_size:         Maximum number of items to return (default 25).
            page_token:        Token from a previous page's ``next_page_token``; omit for the first page.
            search:            Case-insensitive substring filter on the workflow name.
            type:              Filter by workflow type: ``"task"`` or ``"workflow"``.
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
        params = _workflows_list_params(
            page_size, page_token, search, type, view, include_variation
        )
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, self._ops.list, query=params
            ),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "workflows",
            _parse_workflow,
            lambda cur: self._list_page(
                page_size, cur, search, type, view, include_variation
            ),
        )

    async def get(
        self,
        workflow_id: Union[int, str],
        *,
        view: Optional[VariationView] = None,
    ) -> Agent:
        """Retrieve a Modus workflow with full configuration."""
        validate_id(workflow_id, name="workflow_id")
        query = {} if view is None else {"view": view}
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.get,
                path_params={"id": workflow_id},
                query=query or None,
            ),
            self._config.max_retries,
        )
        return _parse_workflow(data)

    def interfaces(self, workflow_id: Union[int, str]) -> AsyncWorkflowInterfacesResource:
        """Return the interfaces sub-resource scoped to ``workflow_id``."""
        return AsyncWorkflowInterfacesResource(self._http, self._config, workflow_id)

    async def create(self, name: str, type: AgentType, *,
                     description: Optional[str] = None,
                     trigger: Optional[TriggerInput] = None,
                     agent_selection: Optional[AgentSelectionInput] = None,
                     workflow_structure: Optional[WorkflowGraphInput] = None,
                     guardrails: Optional[List[str]] = None) -> Agent:
        """Create a new Modus workflow.

        Args:
            name: Display name for the workflow.
            type: ``"task"`` for single-step skill orchestration, or ``"workflow"``
                  for a multi-step graph.
            guardrails: Runtime guardrail labels (for example ``\"no-pii\"``).
                When set, the workflow is created with these labels under the
                organisation default sharing rules. Omit (``None``) to create
                with no guardrails. ACL fields cannot be set from the SDK.
        """
        body = _WorkflowCreateBody(
            name=name, type=type, description=description,
            trigger=dump_trigger(trigger),
            agent_selection=dump_agent_selection(agent_selection),
            workflow_structure=dump_workflow_structure(workflow_structure),
            access_config=access_config_body_for_create(guardrails),
        ).model_dump(by_alias=True, exclude_none=True)
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, self._ops.create, json_body=body
            ),
            self._config.max_retries,
        )
        return _parse_workflow(raw)

    async def update(self, workflow_id: Union[int, str], *,
                     name: Optional[str] = None, type: Optional[AgentType] = None,
                     description: Optional[str] = None,
                     trigger: Optional[TriggerInput] = None,
                     agent_selection: Optional[AgentSelectionInput] = None,
                     workflow_structure: Optional[WorkflowGraphInput] = None,
                     guardrails: Optional[List[str]] = None,
                     update_mask: Optional[str] = None) -> Agent:
        """Update a Modus workflow's configuration.

        Only the fields you pass are changed. To clear a field, name it in
        ``update_mask`` (a comma-separated list of field names) and leave its
        argument unset — the server sets each masked field to null and leaves
        fields not named in the mask untouched.

        Args:
            guardrails: Runtime guardrail labels to set on the workflow. Fetches
                the current workflow first and merges these labels into its access
                configuration (an extra ``get`` request). Omit (``None``) to
                leave guardrails unchanged. Pass ``[]`` to clear all guardrails.
        """
        validate_id(workflow_id, name="workflow_id")
        if guardrails is not None:
            existing = await async_with_retry(
                lambda: invoke_operation_async(
                    self._http,
                    self._ops.get,
                    path_params={"id": workflow_id},
                ),
                self._config.max_retries,
            )
            access_config = access_config_body_for_update(guardrails, lambda: existing)
        else:
            access_config = None
        body = _WorkflowUpdateBody(
            name=name, type=type, description=description,
            trigger=dump_trigger(trigger),
            agent_selection=dump_agent_selection(agent_selection),
            workflow_structure=dump_workflow_structure(workflow_structure),
            access_config=access_config,
        ).model_dump(by_alias=True, exclude_none=update_mask is None)
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.update,
                path_params={"id": workflow_id},
                query=update_mask_query(update_mask),
                json_body=body,
            ),
            self._config.max_retries,
        )
        return _parse_workflow(raw)

    async def deploy(self, workflow_id: Union[int, str]) -> Agent:
        validate_id(workflow_id, name="workflow_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.deploy,
                path_params={"id": workflow_id},
                json_body={},
            ),
            self._config.max_retries,
            retry_not_found_on_deploy=True,
        )
        return _parse_deploy_workflow(raw)

    async def toggle(self, workflow_id: Union[int, str], *, active: bool) -> Agent:
        validate_id(workflow_id, name="workflow_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, self._ops.toggle, path_params={"id": workflow_id},
                json_body={"active": active},
            ),
            self._config.max_retries,
        )
        return _parse_workflow(raw)

    async def delete(self, workflow_id: Union[int, str]) -> None:
        validate_id(workflow_id, name="workflow_id")
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.delete,
                path_params={"id": workflow_id},
            ),
            self._config.max_retries,
        )

    async def request_ownership_transfer(
        self, workflow_id: Union[int, str], *, new_owner_user_id: str,
    ) -> Agent:
        """Start transferring ownership of a workflow to another organisation member."""
        validate_id(workflow_id, name="workflow_id")
        body = TransferOwnershipDto(new_owner_user_id=new_owner_user_id)
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.request_ownership_transfer,
                path_params={"id": workflow_id},
                json_body=body.model_dump(by_alias=True, exclude_none=True),
            ),
            self._config.max_retries,
        )
        return _parse_workflow(raw)

    async def cancel_ownership_transfer(self, workflow_id: Union[int, str]) -> Agent:
        """Cancel a pending workflow ownership transfer."""
        validate_id(workflow_id, name="workflow_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.cancel_ownership_transfer,
                path_params={"id": workflow_id},
            ),
            self._config.max_retries,
        )
        return _parse_workflow(raw)

    async def accept_ownership_transfer(self, workflow_id: Union[int, str]) -> Agent:
        """Accept a pending workflow ownership transfer."""
        validate_id(workflow_id, name="workflow_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.accept_ownership_transfer,
                path_params={"id": workflow_id},
                json_body={},
            ),
            self._config.max_retries,
        )
        return _parse_workflow(raw)

    async def restore(self, workflow_id: Union[int, str]) -> Agent:
        """Restore a deleted workflow."""
        validate_id(workflow_id, name="workflow_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.restore,
                path_params={"id": workflow_id},
                json_body={},
            ),
            self._config.max_retries,
        )
        return _parse_workflow(raw)
