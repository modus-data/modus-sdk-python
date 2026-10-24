# Auto-generated from the Modus API schema. Do not edit by hand.

from __future__ import annotations

from typing import Optional

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._pagination import aip_list_params, build_aip_page_mapped, build_async_aip_page_mapped
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_page_size
from modus.types.connections import Connection
from modus.types.pagination import AsyncPage, Page


class _ConnectionsResourceBase:
    """Generated base for the consumption ``connections`` resource."""

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
        List connections.

        Returns a paginated page of warehouse and SaaS integration connections the caller can
        ``use``. Connections the caller cannot access are filtered out. Use the returned ``id`` when
        creating saved-query context items. Pagination uses an opaque token returned in
        ``next_page_token``.

        **Requires:** ``context:read``

        Args:
            page_size: Items per page. Defaults to 25.
            page_token: Opaque page token from a previous response's ``next_page_token``. Omit for
                the first page.
            type: Filter by effective integration category (case-sensitive exact match).

        Returns:
            A page of connections.
        """
        validate_page_size(page_size)
        return self._list_page(page_size, page_token, type)

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        type: Optional[str],
    ) -> Page[Connection]:
        params = aip_list_params(page_size, page_token)
        if type is not None:
            params["type"] = type
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "ConnectionsController_list",
                query=params,
            ),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "connections",
            Connection.model_validate,
            lambda cur: self._list_page(page_size, cur, type),
        )


class _AsyncConnectionsResourceBase:
    """Generated base for the consumption ``connections`` resource."""

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
        List connections.

        Returns a paginated page of warehouse and SaaS integration connections the caller can
        ``use``. Connections the caller cannot access are filtered out. Use the returned ``id`` when
        creating saved-query context items. Pagination uses an opaque token returned in
        ``next_page_token``.

        **Requires:** ``context:read``

        Args:
            page_size: Items per page. Defaults to 25.
            page_token: Opaque page token from a previous response's ``next_page_token``. Omit for
                the first page.
            type: Filter by effective integration category (case-sensitive exact match).

        Returns:
            A page of connections.
        """
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token, type)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        type: Optional[str],
    ) -> AsyncPage[Connection]:
        params = aip_list_params(page_size, page_token)
        if type is not None:
            params["type"] = type
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ConnectionsController_list",
                query=params,
            ),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "connections",
            Connection.model_validate,
            lambda cur: self._list_page(page_size, cur, type),
        )
