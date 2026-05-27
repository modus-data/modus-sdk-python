"""
Top-level client classes.

Modus      — synchronous client for scripts, notebooks, data pipelines
AsyncModus — asynchronous client for FastAPI, async workflows
"""

from __future__ import annotations
from typing import Optional, Union

import httpx

from ._auth import resolve_api_key, resolve_base_url, resolve_max_retries, resolve_timeout
from ._config import DEFAULT_BASE_URL, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, ModusConfig
from ._http import AsyncHttpClient, HttpClient
from .resources import (
    AgentsResource,
    AsyncAgentsResource,
    AsyncContextResource,
    AsyncSkillsResource,
    ContextResource,
    SkillsResource,
)


class Modus:
    """
    Synchronous Modus API client.

    Instantiate once and reuse across your script or application.
    The client is thread-safe for concurrent GET requests.

    Args:
        api_key:     Your Modus API key. If omitted, reads from the
                     MODUS_API_KEY environment variable.
        base_url:    API base URL. Defaults to https://api.modus.com.
                     Override for local dev: base_url="http://localhost:3080".
        timeout:     Request timeout in seconds (default 60).
        max_retries: Number of automatic retries on 429/5xx (default 2).

    Example:
        import modus

        client = modus.Modus(api_key="modus_xxx")

        for skill in client.skills.list():
            print(skill.name)

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

        self.skills: SkillsResource = SkillsResource(self._http, self._config)
        self.agents: AgentsResource = AgentsResource(self._http, self._config)
        self.context: ContextResource = ContextResource(self._http, self._config)

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> "Modus":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Modus(base_url={self._config.base_url!r})"


class AsyncModus:
    """
    Asynchronous Modus client. Use with async frameworks such as FastAPI, asyncio, or Jupyter.

    Example:
        import modus

        client = modus.AsyncModus(api_key="modus_xxx")

        async def main():
            page = await client.skills.list()
            for skill in page:
                print(skill.name)
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

        self.skills: AsyncSkillsResource = AsyncSkillsResource(self._http, self._config)
        self.agents: AsyncAgentsResource = AsyncAgentsResource(self._http, self._config)
        self.context: AsyncContextResource = AsyncContextResource(self._http, self._config)

    async def aclose(self) -> None:
        """Close the underlying async HTTP connection pool."""
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncModus":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        return f"AsyncModus(base_url={self._config.base_url!r})"
