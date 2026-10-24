"""List data connections available to your organization."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Optional

from ..._generated.resources.consumption.connections import (
    _AsyncConnectionsResourceBase,
    _ConnectionsResourceBase,
)
from ..._openapi_invoke import invoke_operation, invoke_operation_async
from ..._pagination import aip_list_params, build_aip_page_mapped, build_async_aip_page_mapped
from ..._retry import async_with_retry, with_retry
from ..._validation import validate_id, validate_page_size
from ...types.connections import Connection, ConnectionSelection
from ...types.pagination import AsyncPage, Page


class ConnectionsResource(_ConnectionsResourceBase):
    """
    Read access to integration connections.

    client.connections.list()                          → Page[Connection]
    client.connections.find(name=\"...\")              → Connection | None
    client.connections.list_selections(connection_id)  → Page[ConnectionSelection]
    client.connections.iter_selections(connection_id)  → Iterator[ConnectionSelection]
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

    def list_selections(
        self,
        connection_id: str,
        *,
        page_size: Optional[int] = None,
        page_token: Optional[str] = None,
    ) -> Page[ConnectionSelection]:
        """
        List the selectable units on a connection (a repository, a schema, a project).

        Args:
            connection_id: Connection id.
            page_size: Items per page (default 25).
            page_token: Opaque token from a previous page's ``next_page_token``.

        Returns:
            ``Page[ConnectionSelection]``. Use ``iter_selections`` or
            ``.auto_paging_iter()`` to walk every page.

        Example:
            >>> page = client.connections.list_selections(
            ...     "7a3f9d2c-1111-4000-a000-000000000abc"
            ... )
            >>> for unit in page.auto_paging_iter():
            ...     print(unit.object_type, unit.path)
        """
        validate_id(connection_id, name="connection_id")
        size = 25 if page_size is None else page_size
        validate_page_size(size)
        return self._list_selections_page(connection_id, size, page_token)

    def _list_selections_page(
        self,
        connection_id: str,
        page_size: int,
        page_token: Optional[str],
    ) -> Page[ConnectionSelection]:
        params = aip_list_params(page_size, page_token)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "ConnectionsController_listSelections",
                path_params={"connectionId": connection_id},
                query=params,
            ),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "selections",
            ConnectionSelection.model_validate,
            lambda cur: self._list_selections_page(connection_id, page_size, cur),
        )

    def iter_selections(
        self,
        connection_id: str,
        *,
        page_size: Optional[int] = None,
    ) -> Iterator[ConnectionSelection]:
        """
        Yield every selectable unit on a connection, following pages.

        Args:
            connection_id: Connection id.
            page_size: Items per page (default 25).

        Example:
            >>> for unit in client.connections.iter_selections(
            ...     "7a3f9d2c-1111-4000-a000-000000000abc"
            ... ):
            ...     print(unit.object_type, unit.display_name)
        """
        yield from self.list_selections(connection_id, page_size=page_size).auto_paging_iter()


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

    async def list_selections(
        self,
        connection_id: str,
        *,
        page_size: Optional[int] = None,
        page_token: Optional[str] = None,
    ) -> AsyncPage[ConnectionSelection]:
        """
        List the selectable units on a connection (a repository, a schema, a project).

        Args:
            connection_id: Connection id.
            page_size: Items per page (default 25).
            page_token: Opaque token from a previous page's ``next_page_token``.

        Returns:
            ``AsyncPage[ConnectionSelection]``. Use ``iter_selections`` or
            ``.auto_paging_iter()`` to walk every page.

        Example:
            >>> page = await client.connections.list_selections(
            ...     "7a3f9d2c-1111-4000-a000-000000000abc"
            ... )
            >>> async for unit in page.auto_paging_iter():
            ...     print(unit.object_type, unit.path)
        """
        validate_id(connection_id, name="connection_id")
        size = 25 if page_size is None else page_size
        validate_page_size(size)
        return await self._list_selections_page(connection_id, size, page_token)

    async def _list_selections_page(
        self,
        connection_id: str,
        page_size: int,
        page_token: Optional[str],
    ) -> AsyncPage[ConnectionSelection]:
        params = aip_list_params(page_size, page_token)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ConnectionsController_listSelections",
                path_params={"connectionId": connection_id},
                query=params,
            ),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "selections",
            ConnectionSelection.model_validate,
            lambda cur: self._list_selections_page(connection_id, page_size, cur),
        )

    async def iter_selections(
        self,
        connection_id: str,
        *,
        page_size: Optional[int] = None,
    ) -> AsyncIterator[ConnectionSelection]:
        """
        Yield every selectable unit on a connection, following pages.

        Args:
            connection_id: Connection id.
            page_size: Items per page (default 25).

        Example:
            >>> async for unit in client.connections.iter_selections(
            ...     "7a3f9d2c-1111-4000-a000-000000000abc"
            ... ):
            ...     print(unit.object_type, unit.display_name)
        """
        page = await self.list_selections(connection_id, page_size=page_size)
        async for unit in page.auto_paging_iter():
            yield unit
