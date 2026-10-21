"""List data connections available to your organization."""

from __future__ import annotations

from typing import Optional

from ..._generated.resources.consumption.connections import (
    _AsyncConnectionsResourceBase,
    _ConnectionsResourceBase,
)
from ...types.connections import Connection


class ConnectionsResource(_ConnectionsResourceBase):
    """
    Read access to integration connections.

    client.connections.list()              → Page[Connection]
    client.connections.find(name=\"...\")  → Connection | None
    """

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


class AsyncConnectionsResource(_AsyncConnectionsResourceBase):
    """Async read access to integration connections."""

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
