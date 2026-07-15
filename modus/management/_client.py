"""
ModusManagement — synchronous client for managing Modus scopes, workflows, and context.
AsyncModusManagement — asynchronous client for the same.
"""

from __future__ import annotations

from typing import Optional, Union

import httpx

from modus._auth import resolve_api_key, resolve_base_url, resolve_max_retries, resolve_timeout
from modus._config import DEFAULT_BASE_URL, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, ModusConfig
from modus._http import AsyncHttpClient, HttpClient

from .resources import (
    AsyncContextResource,
    AsyncOrganizationResource,
    AsyncScopesResource,
    AsyncUsageResource,
    AsyncUsersResource,
    AsyncWorkflowsResource,
    ContextResource,
    OrganizationResource,
    ScopesResource,
    UsageResource,
    UsersResource,
    WorkflowsResource,
)


class ModusManagement:
    """
    Synchronous Modus management client.

    Instantiate once and reuse. Thread-safe for concurrent reads.

    Args:
        api_key:     Your Modus API key (requires scopes:write + workflows:write scopes).
                     Falls back to MODUS_API_KEY env var.
        base_url:    API origin without a path suffix (default
                     https://api.modus.com).
        timeout:     Request timeout as seconds or httpx.Timeout. Default is
                     5s connect and 300s read.
        max_retries: Retries on 429/5xx (default 2).

    Example:
        from modus.management import ModusManagement

        client = ModusManagement(api_key="modus_xxx")

        scope = client.scopes.create(
            name="Snowflake Analyst",
            instructions=["Answer data questions using Snowflake."],
            model="gpt-4o",
        )
        client.scopes.deploy(scope.id)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: Union[float, httpx.Timeout, None] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        resolved_key = resolve_api_key(api_key)
        resolved_url = resolve_base_url(base_url) or DEFAULT_BASE_URL
        _t = resolve_timeout(timeout)
        resolved_timeout = _t if _t is not None else DEFAULT_TIMEOUT
        resolved_retries = resolve_max_retries(max_retries)
        if resolved_retries is None:
            resolved_retries = DEFAULT_MAX_RETRIES

        self._config = ModusConfig(
            api_key=resolved_key,
            base_url=resolved_url,
            timeout=resolved_timeout,
            max_retries=resolved_retries,
        )
        self._http = HttpClient(self._config)

        self.scopes: ScopesResource = ScopesResource(self._http, self._config)
        self.workflows: WorkflowsResource = WorkflowsResource(self._http, self._config)
        self.context: ContextResource = ContextResource(self._http, self._config)
        self.usage: UsageResource = UsageResource(self._http, self._config)
        self.users: UsersResource = UsersResource(self._http, self._config)
        self.organization: OrganizationResource = OrganizationResource(self._http, self._config)

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> "ModusManagement":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"ModusManagement(base_url={self._config.base_url!r})"


class AsyncModusManagement:
    """
    Asynchronous Modus management client.

    Args:
        api_key:     Modus API key with write scopes. Falls back to MODUS_API_KEY.
        base_url:    API origin without a path suffix (default
                     https://api.modus.com).
        timeout:     Request timeout as seconds or httpx.Timeout. Default is
                     5s connect and 300s read.
        max_retries: Retries on 429/5xx (default 2).

    Example:
        client = AsyncModusManagement(api_key="modus_xxx")
        async def main():
            scope = await client.scopes.create(name="Analyst", model="gpt-4o")
            await client.aclose()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: Union[float, httpx.Timeout, None] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        resolved_key = resolve_api_key(api_key)
        resolved_url = resolve_base_url(base_url) or DEFAULT_BASE_URL
        _t = resolve_timeout(timeout)
        resolved_timeout = _t if _t is not None else DEFAULT_TIMEOUT
        resolved_retries = resolve_max_retries(max_retries)
        if resolved_retries is None:
            resolved_retries = DEFAULT_MAX_RETRIES

        self._config = ModusConfig(
            api_key=resolved_key,
            base_url=resolved_url,
            timeout=resolved_timeout,
            max_retries=resolved_retries,
        )
        self._http = AsyncHttpClient(self._config)

        self.scopes: AsyncScopesResource = AsyncScopesResource(self._http, self._config)
        self.workflows: AsyncWorkflowsResource = AsyncWorkflowsResource(self._http, self._config)
        self.context: AsyncContextResource = AsyncContextResource(self._http, self._config)
        self.usage: AsyncUsageResource = AsyncUsageResource(self._http, self._config)
        self.users: AsyncUsersResource = AsyncUsersResource(self._http, self._config)
        self.organization: AsyncOrganizationResource = AsyncOrganizationResource(
            self._http, self._config
        )

    async def aclose(self) -> None:
        """Close the underlying async HTTP connection pool."""
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncModusManagement":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        return f"AsyncModusManagement(base_url={self._config.base_url!r})"
