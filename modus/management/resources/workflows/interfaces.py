"""Manage interfaces attached to a workflow."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Union

from modus._generated.models import (
    AddAgentInterfaceDto,
    AgentInterfaceDto,
    UpdateAgentInterfaceDto,
)
from modus._generated.resources.management.workflows.interfaces import (
    _AsyncWorkflowsInterfacesResourceBase,
    _WorkflowsInterfacesResourceBase,
)
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._query import update_mask_query
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id


def _add_interface_body(interface: Union[AddAgentInterfaceDto, Mapping[str, Any]]) -> dict[str, Any]:
    """Accept a DTO or plain mapping (TS parity)."""
    if isinstance(interface, AddAgentInterfaceDto):
        model = interface
    else:
        model = AddAgentInterfaceDto.model_validate(interface)
    return model.model_dump(by_alias=True, exclude_none=True)


class WorkflowInterfacesResource(_WorkflowsInterfacesResourceBase):

    def create(self, interface: Union[AddAgentInterfaceDto, Mapping[str, Any]]) -> AgentInterfaceDto:
        """Add an interface to this workflow.

        Args:
            interface: Interface configuration to attach, as a DTO or plain mapping.
        """
        validate_id(self._workflow_id, name="workflow_id")
        raw = with_retry(lambda: invoke_operation(
            self._http, "WorkflowInterfacesController_add", path_params={"id": self._workflow_id},
            json_body=_add_interface_body(interface),
        ), self._config.max_retries)
        return AgentInterfaceDto.model_validate(raw)

    def update(self, interface_id: str, interface: UpdateAgentInterfaceDto, *,
               update_mask: Optional[str] = None) -> AgentInterfaceDto:
        """Update an interface attached to this workflow."""
        validate_id(self._workflow_id, name="workflow_id")
        validate_id(interface_id, name="interface_id")
        raw = with_retry(lambda: invoke_operation(
            self._http, "WorkflowInterfacesController_update",
            path_params={"id": self._workflow_id, "interfaceId": interface_id},
            query=update_mask_query(update_mask),
            json_body=interface.model_dump(by_alias=True, exclude_none=update_mask is None),
        ), self._config.max_retries)
        return AgentInterfaceDto.model_validate(raw)


class AsyncWorkflowInterfacesResource(_AsyncWorkflowsInterfacesResourceBase):

    async def create(self, interface: Union[AddAgentInterfaceDto, Mapping[str, Any]]) -> AgentInterfaceDto:
        """Add an interface to this workflow.

        Args:
            interface: Interface configuration to attach, as a DTO or plain mapping.
        """
        validate_id(self._workflow_id, name="workflow_id")
        raw = await async_with_retry(lambda: invoke_operation_async(
            self._http, "WorkflowInterfacesController_add", path_params={"id": self._workflow_id},
            json_body=_add_interface_body(interface),
        ), self._config.max_retries)
        return AgentInterfaceDto.model_validate(raw)

    async def update(self, interface_id: str, interface: UpdateAgentInterfaceDto, *,
                     update_mask: Optional[str] = None) -> AgentInterfaceDto:
        """Update an interface attached to this workflow.

        Args:
            interface_id: Identifier of the interface to update.
            interface: Updated interface values.
            update_mask: Optional comma-separated list of fields to update.
        """
        validate_id(self._workflow_id, name="workflow_id")
        validate_id(interface_id, name="interface_id")
        raw = await async_with_retry(lambda: invoke_operation_async(
            self._http, "WorkflowInterfacesController_update",
            path_params={"id": self._workflow_id, "interfaceId": interface_id},
            query=update_mask_query(update_mask),
            json_body=interface.model_dump(by_alias=True, exclude_none=update_mask is None),
        ), self._config.max_retries)
        return AgentInterfaceDto.model_validate(raw)
