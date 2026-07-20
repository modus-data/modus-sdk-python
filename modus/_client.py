"""
Top-level client classes.

Modus      — synchronous client for scripts, notebooks, data pipelines
AsyncModus — asynchronous client for FastAPI, async workflows
"""

from __future__ import annotations

from typing import Mapping, Optional, Union

import httpx

from ._auth import (
    resolve_agent_host,
    resolve_api_key,
    resolve_base_url,
    resolve_max_retries,
    resolve_organization_id,
    resolve_timeout,
)
from ._config import (
    DEFAULT_AGENT_HOST,
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    ModusConfig,
)
from ._http import AsyncHttpClient, HttpClient
from .resources import (
    AsyncConnectionsResource,
    AsyncContextResource,
    AsyncModusResource,
    AsyncScopesResource,
    AsyncSuggestionsResource,
    AsyncWorkflowsResource,
    ConnectionsResource,
    ContextResource,
    ModusResource,
    ScopesResource,
    SuggestionsResource,
    WorkflowsResource,
)


class Modus:
    """
    Synchronous Modus API client.

    Instantiate once and reuse across your script or application.
    The client is thread-safe for concurrent GET requests.

    Args:
        api_key:     Your Modus API key. If omitted, reads from the
                     MODUS_API_KEY environment variable.
        base_url:    API origin without a path suffix (default
                     https://api.getmodus.com).
        agent_host:  Agent host origin for streaming runs (default
                     https://agent.getmodus.com). Override via argument or
                     MODUS_AGENT_HOST.
        organization_id: Optional Clerk org id for agent-host run bodies.
                     Usually omit — agent-service uses the PAT principal org.
                     Override via MODUS_ORGANIZATION_ID when needed.
        base_urls:   Optional service-specific API origins.
        timeout:     Request timeout as seconds or httpx.Timeout. Default is
                     5s connect and 300s read.
        max_retries: Number of automatic retries on 429/5xx (default 2).

    Example:
        import modus

        client = modus.Modus(api_key="modus_xxx")

        for scope in client.scopes.list():
            print(scope.name)

        # Write operations use the management client in the same package:
        from modus.management import ModusManagement

        mgmt = ModusManagement(api_key="modus_xxx")
        mgmt.context.create_note(
            title="Fiscal Year",
            content="Runs Feb 1 – Jan 31.",
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        agent_host: Optional[str] = None,
        organization_id: Optional[str] = None,
        base_urls: Optional[Mapping[str, str]] = None,
        timeout: Union[float, httpx.Timeout, None] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        resolved_key = resolve_api_key(api_key)
        resolved_url = resolve_base_url(base_url) or DEFAULT_BASE_URL
        # Same precedence as TS: base_urls['agent-service'] drives streaming too.
        resolved_agent_host = (
            (base_urls or {}).get("agent-service")
            or resolve_agent_host(agent_host)
            or DEFAULT_AGENT_HOST
        )
        resolved_org = resolve_organization_id(organization_id)
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
            agent_host=resolved_agent_host,
            organization_id=resolved_org,
            base_urls=base_urls or {},
        )
        self._http = HttpClient(self._config)
        # Dedicated HTTP client for streaming to the agent host.
        _agent_config = ModusConfig(
            api_key=resolved_key,
            base_url=resolved_agent_host,
            timeout=resolved_timeout,
            max_retries=resolved_retries,
            agent_host=resolved_agent_host,
            organization_id=resolved_org,
        )
        self._agent_http: HttpClient = HttpClient(_agent_config)

        self.scopes: ScopesResource = ScopesResource(self._http, self._agent_http, self._config)
        self.modus: ModusResource = ModusResource(self._http, self._agent_http, self._config)
        self.workflows: WorkflowsResource = WorkflowsResource(
            self._http, self._agent_http, self._config
        )
        self.context: ContextResource = ContextResource(self._http, self._config)
        self.connections: ConnectionsResource = ConnectionsResource(self._http, self._config)
        self.suggestions: SuggestionsResource = SuggestionsResource(self._http, self._config)

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()
        if self._agent_http is not self._http:
            self._agent_http.close()

    def __enter__(self) -> "Modus":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Modus(base_url={self._config.base_url!r})"


class AsyncModus:
    """
    Asynchronous Modus API client.

    Args:
        api_key:     Your Modus API key. If omitted, reads from MODUS_API_KEY.
        base_url:    API origin without a path suffix (default
                     https://api.getmodus.com).
        agent_host:  Agent host origin for streaming runs (default
                     https://agent.getmodus.com). Override via argument or
                     MODUS_AGENT_HOST.
        organization_id: Optional Clerk org id for agent-host run bodies.
        base_urls:   Optional service-specific API origins.
        timeout:     Request timeout as seconds or httpx.Timeout. Default is
                     5s connect and 300s read.
        max_retries: Retries on 429/5xx (default 2).

    Example:
        import modus

        client = modus.AsyncModus(api_key="modus_xxx")

        async def main():
            page = await client.scopes.list()
            for scope in page:
                print(scope.name)
            await client.aclose()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        agent_host: Optional[str] = None,
        organization_id: Optional[str] = None,
        base_urls: Optional[Mapping[str, str]] = None,
        timeout: Union[float, httpx.Timeout, None] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        resolved_key = resolve_api_key(api_key)
        resolved_url = resolve_base_url(base_url) or DEFAULT_BASE_URL
        # Same precedence as TS: base_urls['agent-service'] drives streaming too.
        resolved_agent_host = (
            (base_urls or {}).get("agent-service")
            or resolve_agent_host(agent_host)
            or DEFAULT_AGENT_HOST
        )
        resolved_org = resolve_organization_id(organization_id)
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
            agent_host=resolved_agent_host,
            organization_id=resolved_org,
            base_urls=base_urls or {},
        )
        self._http = AsyncHttpClient(self._config)
        _agent_config = ModusConfig(
            api_key=resolved_key,
            base_url=resolved_agent_host,
            timeout=resolved_timeout,
            max_retries=resolved_retries,
            agent_host=resolved_agent_host,
            organization_id=resolved_org,
        )
        self._agent_http: AsyncHttpClient = AsyncHttpClient(_agent_config)

        self.scopes: AsyncScopesResource = AsyncScopesResource(
            self._http, self._agent_http, self._config
        )
        self.modus: AsyncModusResource = AsyncModusResource(self._http, self._agent_http, self._config)
        self.workflows: AsyncWorkflowsResource = AsyncWorkflowsResource(
            self._http, self._agent_http, self._config
        )
        self.context: AsyncContextResource = AsyncContextResource(self._http, self._config)
        self.connections: AsyncConnectionsResource = AsyncConnectionsResource(
            self._http, self._config
        )
        self.suggestions: AsyncSuggestionsResource = AsyncSuggestionsResource(
            self._http, self._config
        )

    async def aclose(self) -> None:
        """Close the underlying async HTTP connection pool."""
        await self._http.aclose()
        if self._agent_http is not self._http:
            await self._agent_http.aclose()

    async def __aenter__(self) -> "AsyncModus":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        return f"AsyncModus(base_url={self._config.base_url!r})"
