"""Manage Slack and Microsoft Teams interfaces on a scope."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Union

from modus._generated.models import (
    AddScopeInterfaceDto,
    ScopeInterfaceDto,
    UpdateScopeInterfaceDto,
)
from modus._generated.resources.management.scopes.interfaces import (
    _AsyncScopesInterfacesResourceBase,
    _ScopesInterfacesResourceBase,
)
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._query import update_mask_query
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id


def _add_body(interface: Union[AddScopeInterfaceDto, Mapping[str, Any]]) -> dict[str, Any]:
    model = interface if isinstance(interface, AddScopeInterfaceDto) else AddScopeInterfaceDto.model_validate(interface)
    return model.model_dump(by_alias=True, exclude_none=True)


class ScopeInterfacesResource(_ScopesInterfacesResourceBase):

    def create(self, interface: Union[AddScopeInterfaceDto, Mapping[str, Any]]) -> ScopeInterfaceDto:
        """Add a Slack or Microsoft Teams interface to this scope.

        Args:
            interface: Interface type, optional name and config, as a DTO or plain mapping.
        """
        validate_id(self._scope_id, name="scope_id")
        raw = with_retry(lambda: invoke_operation(
            self._http, "ScopeInterfacesController_add", path_params={"id": self._scope_id},
            json_body=_add_body(interface),
        ), self._config.max_retries)
        return ScopeInterfaceDto.model_validate(raw)

    def update(self, interface_id: str, interface: UpdateScopeInterfaceDto, *,
               update_mask: Optional[str] = None) -> ScopeInterfaceDto:
        """Update an interface on this scope.

        Args:
            interface_id: Identifier of the interface to update.
            interface: Updated name and/or config.
            update_mask: Optional comma-separated list of fields to update.
        """
        validate_id(self._scope_id, name="scope_id")
        validate_id(interface_id, name="interface_id")
        raw = with_retry(lambda: invoke_operation(
            self._http, "ScopeInterfacesController_update",
            path_params={"id": self._scope_id, "interfaceId": interface_id},
            query=update_mask_query(update_mask),
            json_body=interface.model_dump(by_alias=True, exclude_none=True),
        ), self._config.max_retries)
        return ScopeInterfaceDto.model_validate(raw)


class AsyncScopeInterfacesResource(_AsyncScopesInterfacesResourceBase):

    async def create(self, interface: Union[AddScopeInterfaceDto, Mapping[str, Any]]) -> ScopeInterfaceDto:
        """Add a Slack or Microsoft Teams interface to this scope.

        Args:
            interface: Interface type, optional name and config, as a DTO or plain mapping.
        """
        validate_id(self._scope_id, name="scope_id")
        raw = await async_with_retry(lambda: invoke_operation_async(
            self._http, "ScopeInterfacesController_add", path_params={"id": self._scope_id},
            json_body=_add_body(interface),
        ), self._config.max_retries)
        return ScopeInterfaceDto.model_validate(raw)

    async def update(self, interface_id: str, interface: UpdateScopeInterfaceDto, *,
                     update_mask: Optional[str] = None) -> ScopeInterfaceDto:
        """Update an interface on this scope.

        Args:
            interface_id: Identifier of the interface to update.
            interface: Updated name and/or config.
            update_mask: Optional comma-separated list of fields to update.
        """
        validate_id(self._scope_id, name="scope_id")
        validate_id(interface_id, name="interface_id")
        raw = await async_with_retry(lambda: invoke_operation_async(
            self._http, "ScopeInterfacesController_update",
            path_params={"id": self._scope_id, "interfaceId": interface_id},
            query=update_mask_query(update_mask),
            json_body=interface.model_dump(by_alias=True, exclude_none=True),
        ), self._config.max_retries)
        return ScopeInterfaceDto.model_validate(raw)
