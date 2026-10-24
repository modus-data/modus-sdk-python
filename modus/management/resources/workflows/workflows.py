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
from modus._generated.resources.management.workflows import (
    _AsyncWorkflowsResourceBase,
    _WorkflowsResourceBase,
)
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._query import update_mask_query
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id
from modus.types.agents import Agent, AgentType
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


class WorkflowsResource(_WorkflowsResourceBase):
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
        super().__init__(http, config, ops)
        self._ops: ManagementWorkflowsOperations = ops

    def get(
        self,
        workflow_id: Union[int, str],
        *,
        view: Optional[VariationView] = None,
    ) -> Agent:
        """
        Retrieve a Modus workflow with full configuration.

        Args:
            workflow_id: Workflow numeric id or slug string.
            view:        Variation view — ``"active"`` (deployed) or ``"draft"``.

        Returns:
            Workflow record (``id``, ``name``, ``status``, …).

        Example:
            >>> mgmt = modus.management.ModusManagement()
            >>> wf = mgmt.workflows.get("weekly-digest")
            >>> print(wf.name, wf.status)
        """
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
            description: Optional human-readable description.
            trigger: Optional trigger configuration payload.
            agent_selection: Optional scope/skill selection for task workflows.
            workflow_structure: Optional multi-step graph for ``\"workflow\"`` type.
            guardrails: Runtime guardrail labels (for example ``\"no-pii\"``).
                When set, the workflow is created with these labels under the
                organisation default sharing rules. Omit (``None``) to create
                with no guardrails. ACL fields cannot be set from the SDK.

        Returns:
            The created workflow (draft).

        Example:
            >>> mgmt = modus.management.ModusManagement()
            >>> wf = mgmt.workflows.create("Daily report", "task")
            >>> print(wf.id, wf.name)
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
            workflow_id: Workflow numeric id or slug string.
            name: Optional new display name.
            type: Optional new type (``\"task\"`` or ``\"workflow\"``).
            description: Optional new description.
            trigger: Optional trigger configuration payload.
            agent_selection: Optional scope/skill selection for task workflows.
            workflow_structure: Optional multi-step graph for ``\"workflow\"`` type.
            guardrails: Runtime guardrail labels to set on the workflow. Fetches
                the current workflow first and merges these labels into its access
                configuration (an extra ``get`` request). Omit (``None``) to
                leave guardrails unchanged. Pass ``[]`` to clear all guardrails.
            update_mask: Comma-separated field names to update or clear.

        Returns:
            The updated workflow.

        Example:
            >>> mgmt = modus.management.ModusManagement()
            >>> wf = mgmt.workflows.update(
            ...     "PLACEHOLDER_WORKFLOW_ID",
            ...     description="Runs every morning",
            ... )
            >>> print(wf.description)
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
        """Publish the current draft of a Modus workflow.

        Args:
            workflow_id: Workflow to publish.

        Returns:
            The workflow with its newly published configuration.

        Example:
            >>> mgmt = modus.management.ModusManagement()
            >>> mgmt.workflows.update(workflow_id, description="Runs every morning")
            >>> published = mgmt.workflows.deploy(workflow_id)
            >>> print(published.status)
        """
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


class AsyncWorkflowsResource(_AsyncWorkflowsResourceBase):
    def __init__(
        self,
        http: AsyncHttpClient,
        config: ModusConfig,
        ops: "ManagementWorkflowsOperations" = MANAGEMENT_WORKFLOW_OPERATIONS,
    ) -> None:
        super().__init__(http, config, ops)
        self._ops: ManagementWorkflowsOperations = ops

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
        """Publish the current draft of a Modus workflow. See the sync ``deploy`` for argument details."""
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
        """Enable or disable a workflow. See the sync ``toggle`` for argument details."""
        validate_id(workflow_id, name="workflow_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, self._ops.toggle, path_params={"id": workflow_id},
                json_body={"active": active},
            ),
            self._config.max_retries,
        )
        return _parse_workflow(raw)

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
