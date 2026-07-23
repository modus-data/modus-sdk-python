"""Manage interfaces attached to a workflow."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Union

from modus._config import ModusConfig
from modus._generated.models import (
    AddAgentInterfaceDto,
    AgentInterfaceDto,
    ListAgentInterfacesResponseDto,
    UpdateAgentInterfaceDto,
)
from modus._http import AsyncHttpClient, HttpClient
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


class WorkflowInterfacesResource:
    def __init__(self, http: HttpClient, config: ModusConfig, workflow_id: Union[int, str]) -> None:
        self._http, self._config, self._workflow_id = http, config, workflow_id

    def list(self) -> list[AgentInterfaceDto]:
        """List interfaces attached to this workflow."""
        validate_id(self._workflow_id, name="workflow_id")
        raw = with_retry(lambda: invoke_operation(
            self._http, "WorkflowInterfacesController_list", path_params={"id": self._workflow_id},
        ), self._config.max_retries)
        return ListAgentInterfacesResponseDto.model_validate(raw).interfaces

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

    def delete(self, interface_id: str) -> None:
        """Delete an interface from this workflow."""
        validate_id(self._workflow_id, name="workflow_id")
        validate_id(interface_id, name="interface_id")
        with_retry(lambda: invoke_operation(
            self._http, "WorkflowInterfacesController_delete",
            path_params={"id": self._workflow_id, "interfaceId": interface_id},
        ), self._config.max_retries)

    def delete_all(self) -> None:
        """Delete every interface from this workflow."""
        validate_id(self._workflow_id, name="workflow_id")
        with_retry(lambda: invoke_operation(
            self._http, "WorkflowInterfacesController_deleteAll",
            path_params={"id": self._workflow_id},
        ), self._config.max_retries)


class AsyncWorkflowInterfacesResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig, workflow_id: Union[int, str]) -> None:
        self._http, self._config, self._workflow_id = http, config, workflow_id

    async def list(self) -> list[AgentInterfaceDto]:
        """List interfaces attached to this workflow."""
        validate_id(self._workflow_id, name="workflow_id")
        raw = await async_with_retry(lambda: invoke_operation_async(
            self._http, "WorkflowInterfacesController_list", path_params={"id": self._workflow_id},
        ), self._config.max_retries)
        return ListAgentInterfacesResponseDto.model_validate(raw).interfaces

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

    async def delete(self, interface_id: str) -> None:
        """Delete an interface from this workflow.

        Args:
            interface_id: Identifier of the interface to delete.
        """
        validate_id(self._workflow_id, name="workflow_id")
        validate_id(interface_id, name="interface_id")
        await async_with_retry(lambda: invoke_operation_async(
            self._http, "WorkflowInterfacesController_delete",
            path_params={"id": self._workflow_id, "interfaceId": interface_id},
        ), self._config.max_retries)

    async def delete_all(self) -> None:
        """Delete every interface from this workflow."""
        validate_id(self._workflow_id, name="workflow_id")
        await async_with_retry(lambda: invoke_operation_async(
            self._http, "WorkflowInterfacesController_deleteAll",
            path_params={"id": self._workflow_id},
        ), self._config.max_retries)
