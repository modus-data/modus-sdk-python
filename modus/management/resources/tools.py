"""Tool catalog resource."""

from __future__ import annotations

from typing import Optional

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._pagination import aip_list_params, build_aip_page_mapped, build_async_aip_page_mapped
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_page_size
from modus.types.pagination import AsyncPage, Page

from ..types.tools import ToolCatalogEntry


def _parse_tool(raw: object) -> ToolCatalogEntry:
    return ToolCatalogEntry.model_validate(raw)


class ToolsResource:
    """Browse the catalog of tool/integration surfaces a scope can select in its toolset."""

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> Page[ToolCatalogEntry]:
        """
        List known tool/integration surfaces a scope can select in its toolset.

        Args:
            page_size:  Maximum number of items to return (default 25).
            page_token: Token from a previous page's ``next_page_token``; omit for the first page.
        """
        validate_page_size(page_size)
        return self._list_page(page_size, page_token)

    def _list_page(self, page_size: int, page_token: Optional[str]) -> Page[ToolCatalogEntry]:
        params = aip_list_params(page_size, page_token)
        data = with_retry(
            lambda: invoke_operation(self._http, "ToolsController_list", query=params),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "tools",
            _parse_tool,
            lambda cur: self._list_page(page_size, cur),
        )


class AsyncToolsResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
    ) -> AsyncPage[ToolCatalogEntry]:
        """
        List known tool/integration surfaces a scope can select in its toolset.

        Args:
            page_size:  Maximum number of items to return (default 25).
            page_token: Token from a previous page's ``next_page_token``; omit for the first page.
        """
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token)

    async def _list_page(self, page_size: int, page_token: Optional[str]) -> AsyncPage[ToolCatalogEntry]:
        params = aip_list_params(page_size, page_token)
        data = await async_with_retry(
            lambda: invoke_operation_async(self._http, "ToolsController_list", query=params),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "tools",
            _parse_tool,
            lambda cur: self._list_page(page_size, cur),
        )
