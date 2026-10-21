# Auto-generated from the Modus API schema. Do not edit by hand.

from __future__ import annotations

from typing import Optional, Protocol

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._pagination import aip_list_params, build_aip_page_mapped, build_async_aip_page_mapped
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_page_size
from modus.types.agents import Agent, AgentType
from modus.types.pagination import AsyncPage, Page
from modus.types.views import VariationView


class _Operations(Protocol):
    @property
    def list(self) -> str: ...


class _WorkflowsResourceBase:
    """Generated base for the consumption ``workflows`` resource."""

    def __init__(self, http: HttpClient, config: ModusConfig, ops: _Operations) -> None:
        self._http = http
        self._config = config
        self._ops = ops

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        search: Optional[str] = None,
        type: Optional[AgentType] = None,
        view: Optional[VariationView] = None,
        include_variation: Optional[bool] = None,
    ) -> Page[Agent]:
        """
        List workflows.

        Returns a paginated page of workflows the caller can at least ``use``. Workflows the caller
        cannot see are filtered out. Pagination uses an opaque token returned in
        ``next_page_token``.

        **Requires:** ``workflows:read``

        Args:
            page_size: Items per page. Defaults to 25.
            page_token: Opaque page token from a previous response's ``next_page_token``. Omit for
                the first page.
            search: Case-insensitive substring filter on workflow name.
            type: Filter by workflow type.
            view: Variation view. ``active`` reads deployed; ``draft`` reads the latest builder
                snapshot.
            include_variation: Include the requested variation payload (``trigger``,
                ``workflow_structure``, ``agent_selection``) on list rows.

        Returns:
            A page of workflows.

        Example:
            >>> for wf in client.workflows.list(search="digest").auto_paging_iter():
            ...     print(wf.id, wf.name, wf.status)
        """
        validate_page_size(page_size)
        return self._list_page(page_size, page_token, search, type, view, include_variation)

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        search: Optional[str],
        type: Optional[AgentType],
        view: Optional[VariationView],
        include_variation: Optional[bool],
    ) -> Page[Agent]:
        params = aip_list_params(page_size, page_token)
        if search is not None:
            params["search"] = search
        if type is not None:
            params["type"] = type
        if view is not None:
            params["view"] = view
        if include_variation is not None:
            params["includeVariation"] = include_variation
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                self._ops.list,
                query=params,
            ),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "workflows",
            Agent.model_validate,
            lambda cur: self._list_page(page_size, cur, search, type, view, include_variation),
        )


class _AsyncWorkflowsResourceBase:
    """Generated base for the consumption ``workflows`` resource."""

    def __init__(self, http: AsyncHttpClient, config: ModusConfig, ops: _Operations) -> None:
        self._http = http
        self._config = config
        self._ops = ops

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        search: Optional[str] = None,
        type: Optional[AgentType] = None,
        view: Optional[VariationView] = None,
        include_variation: Optional[bool] = None,
    ) -> AsyncPage[Agent]:
        """
        List workflows.

        Returns a paginated page of workflows the caller can at least ``use``. Workflows the caller
        cannot see are filtered out. Pagination uses an opaque token returned in
        ``next_page_token``.

        **Requires:** ``workflows:read``

        Args:
            page_size: Items per page. Defaults to 25.
            page_token: Opaque page token from a previous response's ``next_page_token``. Omit for
                the first page.
            search: Case-insensitive substring filter on workflow name.
            type: Filter by workflow type.
            view: Variation view. ``active`` reads deployed; ``draft`` reads the latest builder
                snapshot.
            include_variation: Include the requested variation payload (``trigger``,
                ``workflow_structure``, ``agent_selection``) on list rows.

        Returns:
            A page of workflows.
        """
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token, search, type, view, include_variation)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        search: Optional[str],
        type: Optional[AgentType],
        view: Optional[VariationView],
        include_variation: Optional[bool],
    ) -> AsyncPage[Agent]:
        params = aip_list_params(page_size, page_token)
        if search is not None:
            params["search"] = search
        if type is not None:
            params["type"] = type
        if view is not None:
            params["view"] = view
        if include_variation is not None:
            params["includeVariation"] = include_variation
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                self._ops.list,
                query=params,
            ),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "workflows",
            Agent.model_validate,
            lambda cur: self._list_page(page_size, cur, search, type, view, include_variation),
        )
