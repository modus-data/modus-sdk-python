"""Manage subordinate scopes supervised by a scope."""

from __future__ import annotations

from typing import Optional, Union

from modus._config import ModusConfig
from modus._generated.models import SetSupervisionRequestDto, SupervisionDto
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id
from modus.types.views import VariationView


class ScopeSupervisionResource:
    def __init__(self, http: HttpClient, config: ModusConfig, scope_id: Union[int, str]) -> None:
        self._http, self._config, self._scope_id = http, config, scope_id

    def get(self, *, view: Optional[VariationView] = None) -> SupervisionDto:
        """Get this scope's supervision configuration."""
        validate_id(self._scope_id, name="scope_id")
        raw = with_retry(lambda: invoke_operation(
            self._http, "ScopeSupervisionController_get", path_params={"id": self._scope_id},
            query=None if view is None else {"view": view},
        ), self._config.max_retries)
        return SupervisionDto.model_validate(raw)

    def set(self, supervision: SetSupervisionRequestDto) -> SupervisionDto:
        """Replace this scope's subordinate scopes."""
        return self._write("ScopeSupervisionController_set", supervision)

    def set_active(self, supervision: SetSupervisionRequestDto) -> SupervisionDto:
        """Replace subordinate scopes on the active scope version."""
        return self._write("ScopeSupervisionController_setActive", supervision)

    def _write(self, operation: str, supervision: SetSupervisionRequestDto) -> SupervisionDto:
        validate_id(self._scope_id, name="scope_id")
        raw = with_retry(lambda: invoke_operation(
            self._http, operation, path_params={"id": self._scope_id},
            json_body=supervision.model_dump(by_alias=True),
        ), self._config.max_retries)
        return SupervisionDto.model_validate(raw)


class AsyncScopeSupervisionResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig, scope_id: Union[int, str]) -> None:
        self._http, self._config, self._scope_id = http, config, scope_id

    async def get(self, *, view: Optional[VariationView] = None) -> SupervisionDto:
        """Get this scope's supervision configuration.

        Args:
            view: Optional scope variation to inspect.
        """
        validate_id(self._scope_id, name="scope_id")
        raw = await async_with_retry(lambda: invoke_operation_async(
            self._http, "ScopeSupervisionController_get", path_params={"id": self._scope_id},
            query=None if view is None else {"view": view},
        ), self._config.max_retries)
        return SupervisionDto.model_validate(raw)

    async def set(self, supervision: SetSupervisionRequestDto) -> SupervisionDto:
        """Replace this scope's subordinate scopes.

        Args:
            supervision: Replacement supervision configuration.
        """
        return await self._write("ScopeSupervisionController_set", supervision)

    async def set_active(self, supervision: SetSupervisionRequestDto) -> SupervisionDto:
        """Replace subordinate scopes on the active scope version.

        Args:
            supervision: Replacement supervision configuration.
        """
        return await self._write("ScopeSupervisionController_setActive", supervision)

    async def _write(self, operation: str, supervision: SetSupervisionRequestDto) -> SupervisionDto:
        validate_id(self._scope_id, name="scope_id")
        raw = await async_with_retry(lambda: invoke_operation_async(
            self._http, operation, path_params={"id": self._scope_id},
            json_body=supervision.model_dump(by_alias=True),
        ), self._config.max_retries)
        return SupervisionDto.model_validate(raw)
