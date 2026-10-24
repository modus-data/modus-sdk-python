# Auto-generated from the Modus API schema. Do not edit by hand.

from __future__ import annotations

from typing import Union

from modus._config import ModusConfig
from modus._generated.models import AgentInterfaceDto, ListAgentInterfacesResponseDto
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id


class _WorkflowsInterfacesResourceBase:
    """Generated base for the management ``workflows.interfaces`` resource."""

    def __init__(self, http: HttpClient, config: ModusConfig, workflow_id: Union[int, str]) -> None:
        self._http = http
        self._config = config
        self._workflow_id = workflow_id

    def list(self) -> list[AgentInterfaceDto]:
        """
        List interfaces attached to a workflow.

        Returns every Slack, MCP, or Teams interface bound to the workflow. Requires manage
        permission on the workflow.

        **Requires:** ``workflows:read``
        """
        validate_id(self._workflow_id, name="workflow_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "WorkflowInterfacesController_list",
                path_params={"id": self._workflow_id},
            ),
            self._config.max_retries,
        )
        return ListAgentInterfacesResponseDto.model_validate(raw).interfaces

    def delete_all(self) -> None:
        """
        Remove every interface from a workflow.

        Deletes all interface rows attached to the workflow. Useful when recreating the interface
        set from scratch.

        **Requires:** ``workflows:write``
        """
        validate_id(self._workflow_id, name="workflow_id")
        with_retry(
            lambda: invoke_operation(
                self._http,
                "WorkflowInterfacesController_deleteAll",
                path_params={"id": self._workflow_id},
            ),
            self._config.max_retries,
        )

    def delete(self, interface_id: str) -> None:
        """
        Remove a workflow interface.

        Deletes one interface row. For MCP interfaces, bound MCP tokens are revoked best-effort.

        **Requires:** ``workflows:write``

        Args:
            interface_id: Interface row id (UUID).
        """
        validate_id(self._workflow_id, name="workflow_id")
        validate_id(interface_id, name="interface_id")
        with_retry(
            lambda: invoke_operation(
                self._http,
                "WorkflowInterfacesController_delete",
                path_params={"id": self._workflow_id, "interfaceId": interface_id},
            ),
            self._config.max_retries,
        )


class _AsyncWorkflowsInterfacesResourceBase:
    """Generated base for the management ``workflows.interfaces`` resource."""

    def __init__(
        self,
        http: AsyncHttpClient,
        config: ModusConfig,
        workflow_id: Union[int, str],
    ) -> None:
        self._http = http
        self._config = config
        self._workflow_id = workflow_id

    async def list(self) -> list[AgentInterfaceDto]:
        """
        List interfaces attached to a workflow.

        Returns every Slack, MCP, or Teams interface bound to the workflow. Requires manage
        permission on the workflow.

        **Requires:** ``workflows:read``
        """
        validate_id(self._workflow_id, name="workflow_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "WorkflowInterfacesController_list",
                path_params={"id": self._workflow_id},
            ),
            self._config.max_retries,
        )
        return ListAgentInterfacesResponseDto.model_validate(raw).interfaces

    async def delete_all(self) -> None:
        """
        Remove every interface from a workflow.

        Deletes all interface rows attached to the workflow. Useful when recreating the interface
        set from scratch.

        **Requires:** ``workflows:write``
        """
        validate_id(self._workflow_id, name="workflow_id")
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "WorkflowInterfacesController_deleteAll",
                path_params={"id": self._workflow_id},
            ),
            self._config.max_retries,
        )

    async def delete(self, interface_id: str) -> None:
        """
        Remove a workflow interface.

        Deletes one interface row. For MCP interfaces, bound MCP tokens are revoked best-effort.

        **Requires:** ``workflows:write``

        Args:
            interface_id: Interface row id (UUID).
        """
        validate_id(self._workflow_id, name="workflow_id")
        validate_id(interface_id, name="interface_id")
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "WorkflowInterfacesController_delete",
                path_params={"id": self._workflow_id, "interfaceId": interface_id},
            ),
            self._config.max_retries,
        )
