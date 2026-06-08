"""Connections resource — GET /api/v1/connections (read-only)."""

from __future__ import annotations

from typing import Optional

from ..._config import ModusConfig
from ..._http import AsyncHttpClient, HttpClient
from ..._pagination import (
    aip_list_params,
    build_aip_page_mapped,
    build_async_aip_page_mapped,
)
from ..._retry import async_with_retry, with_retry
from ..._validation import validate_page_size
from ..._wire.connections import _ConnectionWire
from ...types.connections import Connection
from ...types.pagination import AsyncPage, Page


def _map_connection(raw: dict) -> Connection:
    wire = _ConnectionWire.model_validate(raw)
    return Connection(id=wire.id, name=wire.name, type=wire.type)


def _connections_list_params(
    page_size: int,
    page_token: Optional[str],
    type: Optional[str],
) -> dict:
    extra: dict = {}
    if type is not None:
        extra["type"] = type
    return aip_list_params(page_size, page_token, **extra)


class ConnectionsResource:
    """
    Read access to integration connections.

    client.connections.list()              → Page[Connection]
    client.connections.find(name=\"...\")  → Connection | None
    """

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        type: Optional[str] = None,
    ) -> Page[Connection]:
        """
        List integration connections the caller can use.

        Args:
            page_size:  Items per page (default 25).
            page_token: Opaque token from a previous page's ``next_page_token``.
            type:       Filter by effective integration category (exact match).
        """
        validate_page_size(page_size)
        return self._list_page(page_size, page_token, type)

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        type: Optional[str],
    ) -> Page[Connection]:
        params = _connections_list_params(page_size, page_token, type)
        data = with_retry(
            lambda: self._http.get("/api/v1/connections", params=params),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "connections",
            _map_connection,
            lambda cur: self._list_page(page_size, cur, type),
        )

    def find(
        self,
        *,
        name: str,
        type: Optional[str] = None,
        page_size: int = 25,
    ) -> Optional[Connection]:
        """
        Find the first connection whose name matches ``name`` (case-insensitive).

        Pages through ``list()`` until a match is found or pages are exhausted.
        """
        token: Optional[str] = None
        target = name.strip().lower()
        while True:
            page = self.list(page_size=page_size, page_token=token, type=type)
            for conn in page:
                if conn.name and conn.name.strip().lower() == target:
                    return conn
            token = page.next_page_token
            if not token:
                return None


class AsyncConnectionsResource:
    """Async read access to integration connections."""

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        type: Optional[str] = None,
    ) -> AsyncPage[Connection]:
        """
        List integration connections the caller can use.

        Args:
            page_size:  Items per page (default 25).
            page_token: Opaque token from a previous page's ``next_page_token``.
            type:       Filter by effective integration category (exact match).

        Returns:
            AsyncPage[Connection] — iterate pages via ``next_page_token``; each
            page is fetched through ``_list_page``.
        """
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token, type)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        type: Optional[str],
    ) -> AsyncPage[Connection]:
        params = _connections_list_params(page_size, page_token, type)
        data = await async_with_retry(
            lambda: self._http.get("/api/v1/connections", params=params),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "connections",
            _map_connection,
            lambda cur: self._list_page(page_size, cur, type),
        )

    async def find(
        self,
        *,
        name: str,
        type: Optional[str] = None,
        page_size: int = 25,
    ) -> Optional[Connection]:
        """
        Find the first connection whose name matches ``name`` (case-insensitive).

        Pages through ``list()`` until a match is found or pages are exhausted.

        Args:
            name:       Connection name to match (trimmed and compared case-insensitively).
            type:       Optional category filter passed through to ``list()``.
            page_size:  Page size for each ``list()`` call while searching.

        Returns:
            The matching ``Connection``, or ``None`` if no page contains a match.
        """
        token: Optional[str] = None
        target = name.strip().lower()
        while True:
            page = await self.list(page_size=page_size, page_token=token, type=type)
            for conn in page:
                if conn.name and conn.name.strip().lower() == target:
                    return conn
            token = page.next_page_token
            if not token:
                return None
