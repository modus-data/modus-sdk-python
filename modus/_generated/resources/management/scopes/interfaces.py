# Auto-generated from the Modus API schema. Do not edit by hand.

from __future__ import annotations

from typing import Union

from modus._config import ModusConfig
from modus._generated.models import ListScopeInterfacesResponseDto, ScopeInterfaceDto
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id


class _ScopesInterfacesResourceBase:
    """Generated base for the management ``scopes.interfaces`` resource."""

    def __init__(self, http: HttpClient, config: ModusConfig, scope_id: Union[int, str]) -> None:
        self._http = http
        self._config = config
        self._scope_id = scope_id

    def list(self) -> list[ScopeInterfaceDto]:
        """
        List the chat interfaces of a scope.

        Returns the chat interfaces (at most one per chat platform) that let people use this scope
        from chat. Requires manage permission on the scope, because the config lists allowed emails.

        **Requires:** ``scopes:read``
        """
        validate_id(self._scope_id, name="scope_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopeInterfacesController_list",
                path_params={"id": self._scope_id},
            ),
            self._config.max_retries,
        )
        return ListScopeInterfacesResponseDto.model_validate(raw).interfaces

    def delete(self, interface_id: str) -> None:
        """
        Remove a scope interface.

        Removes one chat interface from the scope. Mentions on that chat platform stop reaching this
        scope immediately.

        **Requires:** ``scopes:write``

        Args:
            interface_id: Interface id (UUID).
        """
        validate_id(self._scope_id, name="scope_id")
        validate_id(interface_id, name="interface_id")
        with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopeInterfacesController_delete",
                path_params={"id": self._scope_id, "interfaceId": interface_id},
            ),
            self._config.max_retries,
        )


class _AsyncScopesInterfacesResourceBase:
    """Generated base for the management ``scopes.interfaces`` resource."""

    def __init__(
        self,
        http: AsyncHttpClient,
        config: ModusConfig,
        scope_id: Union[int, str],
    ) -> None:
        self._http = http
        self._config = config
        self._scope_id = scope_id

    async def list(self) -> list[ScopeInterfaceDto]:
        """
        List the chat interfaces of a scope.

        Returns the chat interfaces (at most one per chat platform) that let people use this scope
        from chat. Requires manage permission on the scope, because the config lists allowed emails.

        **Requires:** ``scopes:read``
        """
        validate_id(self._scope_id, name="scope_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopeInterfacesController_list",
                path_params={"id": self._scope_id},
            ),
            self._config.max_retries,
        )
        return ListScopeInterfacesResponseDto.model_validate(raw).interfaces

    async def delete(self, interface_id: str) -> None:
        """
        Remove a scope interface.

        Removes one chat interface from the scope. Mentions on that chat platform stop reaching this
        scope immediately.

        **Requires:** ``scopes:write``

        Args:
            interface_id: Interface id (UUID).
        """
        validate_id(self._scope_id, name="scope_id")
        validate_id(interface_id, name="interface_id")
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopeInterfacesController_delete",
                path_params={"id": self._scope_id, "interfaceId": interface_id},
            ),
            self._config.max_retries,
        )
