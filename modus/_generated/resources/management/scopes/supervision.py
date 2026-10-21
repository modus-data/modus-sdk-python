# Auto-generated from the Modus API schema. Do not edit by hand.

from __future__ import annotations

from typing import Optional, Union

from modus._config import ModusConfig
from modus._generated.models import SetSupervisionRequestDto, SupervisionDto
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id
from modus.types.views import VariationView


class _ScopesSupervisionResourceBase:
    """Generated base for the management ``scopes.supervision`` resource."""

    def __init__(self, http: HttpClient, config: ModusConfig, scope_id: Union[int, str]) -> None:
        self._http = http
        self._config = config
        self._scope_id = scope_id

    def get(self, *, view: Optional[VariationView] = None) -> SupervisionDto:
        """
        Read the scope subordinate supervision list.

        Returns the list of subordinate scope ids managed by this scope. ``?view=active`` (default)
        reads the deployed supervision set; ``?view=draft`` reads the most recent builder snapshot.
        Returns 404 when the caller cannot at least ``use`` the scope.

        **Requires:** ``scopes:read``

        Args:
            view: Which variation snapshot to read. Defaults to ``active``.
        """
        validate_id(self._scope_id, name="scope_id")
        query: dict = {}
        if view is not None:
            query["view"] = view
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopeSupervisionController_get",
                path_params={"id": self._scope_id},
                query=query,
            ),
            self._config.max_retries,
        )
        return SupervisionDto.model_validate(raw)

    def set(self, supervision: SetSupervisionRequestDto) -> SupervisionDto:
        """
        Replace draft subordinate supervision list.

        Writes the supplied subordinate id list into the draft variation. Replaces the previous list
        fully — supply an empty array to clear all subordinates. Requires manage permission on the
        supervisor; the change is not visible to runners until the scope is deployed.

        **Requires:** ``scopes:write``

        Args:
            supervision: Request body; see :class:`SetSupervisionRequestDto`.
        """
        validate_id(self._scope_id, name="scope_id")
        body = supervision.model_dump(by_alias=True, exclude_none=False)
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopeSupervisionController_set",
                path_params={"id": self._scope_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return SupervisionDto.model_validate(raw)

    def set_active(self, supervision: SetSupervisionRequestDto) -> SupervisionDto:
        """
        Replace active subordinate supervision list.

        Writes directly into the active variation supervision set, bypassing the draft deploy cycle.
        Requires ``scopes:write`` plus manage permission on the supervisor. Use to correct a live
        supervision graph without going through the builder.

        **Requires:** ``scopes:write``

        Args:
            supervision: Request body; see :class:`SetSupervisionRequestDto`.
        """
        validate_id(self._scope_id, name="scope_id")
        body = supervision.model_dump(by_alias=True, exclude_none=False)
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopeSupervisionController_setActive",
                path_params={"id": self._scope_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return SupervisionDto.model_validate(raw)


class _AsyncScopesSupervisionResourceBase:
    """Generated base for the management ``scopes.supervision`` resource."""

    def __init__(
        self,
        http: AsyncHttpClient,
        config: ModusConfig,
        scope_id: Union[int, str],
    ) -> None:
        self._http = http
        self._config = config
        self._scope_id = scope_id

    async def get(self, *, view: Optional[VariationView] = None) -> SupervisionDto:
        """
        Read the scope subordinate supervision list.

        Returns the list of subordinate scope ids managed by this scope. ``?view=active`` (default)
        reads the deployed supervision set; ``?view=draft`` reads the most recent builder snapshot.
        Returns 404 when the caller cannot at least ``use`` the scope.

        **Requires:** ``scopes:read``

        Args:
            view: Which variation snapshot to read. Defaults to ``active``.
        """
        validate_id(self._scope_id, name="scope_id")
        query: dict = {}
        if view is not None:
            query["view"] = view
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopeSupervisionController_get",
                path_params={"id": self._scope_id},
                query=query,
            ),
            self._config.max_retries,
        )
        return SupervisionDto.model_validate(raw)

    async def set(self, supervision: SetSupervisionRequestDto) -> SupervisionDto:
        """
        Replace draft subordinate supervision list.

        Writes the supplied subordinate id list into the draft variation. Replaces the previous list
        fully — supply an empty array to clear all subordinates. Requires manage permission on the
        supervisor; the change is not visible to runners until the scope is deployed.

        **Requires:** ``scopes:write``

        Args:
            supervision: Request body; see :class:`SetSupervisionRequestDto`.
        """
        validate_id(self._scope_id, name="scope_id")
        body = supervision.model_dump(by_alias=True, exclude_none=False)
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopeSupervisionController_set",
                path_params={"id": self._scope_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return SupervisionDto.model_validate(raw)

    async def set_active(self, supervision: SetSupervisionRequestDto) -> SupervisionDto:
        """
        Replace active subordinate supervision list.

        Writes directly into the active variation supervision set, bypassing the draft deploy cycle.
        Requires ``scopes:write`` plus manage permission on the supervisor. Use to correct a live
        supervision graph without going through the builder.

        **Requires:** ``scopes:write``

        Args:
            supervision: Request body; see :class:`SetSupervisionRequestDto`.
        """
        validate_id(self._scope_id, name="scope_id")
        body = supervision.model_dump(by_alias=True, exclude_none=False)
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopeSupervisionController_setActive",
                path_params={"id": self._scope_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return SupervisionDto.model_validate(raw)
