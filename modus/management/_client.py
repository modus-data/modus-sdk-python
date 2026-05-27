"""
ModusManagement — synchronous client for managing Modus skills, agents, and context.
AsyncModusManagement — asynchronous client for the same.
"""

from __future__ import annotations
from typing import Optional, Union

import httpx

from modus._auth import resolve_api_key, resolve_base_url, resolve_max_retries, resolve_timeout
from modus._config import DEFAULT_BASE_URL, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from .resources import (
    AgentsResource,
    AsyncAgentsResource,
    AsyncContextResource,
    AsyncSkillsResource,
    ContextResource,
    SkillsResource,
)


class ModusManagement:
    """
    Synchronous Modus management client.

    Instantiate once and reuse. Thread-safe for concurrent reads.

    Args:
        api_key:     Your Modus API key (requires skills:write + agents:write scopes).
                     Falls back to MODUS_API_KEY env var.
        base_url:    API base URL. Defaults to https://api.modus.com.
        timeout:     Request timeout in seconds (default 60).
        max_retries: Retries on 429/5xx (default 2).

    Example:
        from modus.management import ModusManagement

        client = ModusManagement(api_key="modus_xxx")

        skill = client.skills.create(
            name="Snowflake Analyst",
            instructions=["Answer data questions using Snowflake."],
            model="gpt-4o",
        )
        client.skills.deploy(skill.id)
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

    def __enter__(self) -> "ModusManagement":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"ModusManagement(base_url={self._config.base_url!r})"


class AsyncModusManagement:
    """
    Asynchronous Modus management client.

    Example:
        client = AsyncModusManagement(api_key="modus_xxx")
        async def main():
            skill = await client.skills.create(name="Analyst", model="gpt-4o")
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

    async def __aenter__(self) -> "AsyncModusManagement":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        return f"AsyncModusManagement(base_url={self._config.base_url!r})"
