# Auto-generated from the Modus API schema. Do not edit by hand.

from __future__ import annotations

from typing import Optional, Union

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._pagination import aip_list_params, build_aip_page_mapped, build_async_aip_page_mapped
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id, validate_page_size
from modus.types.pagination import AsyncPage, Page
from modus.types.scopes import Skill
from modus.types.views import VariationView


class _ScopesResourceBase:
    """Generated base for the management ``scopes`` resource."""

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        search: Optional[str] = None,
        view: Optional[VariationView] = None,
        manager_id: Optional[int] = None,
    ) -> Page[Skill]:
        """
        List scopes.

        Returns a paginated page of scopes the caller can at least ``use``. Scopes the caller cannot
        see are filtered out. Pagination uses an opaque token returned in ``next_page_token``.

        **Requires:** ``scopes:read``

        Args:
            page_size: Items per page. Defaults to 25.
            page_token: Opaque page token from a previous response's ``next_page_token``. Omit for
                the first page.
            search: Case-insensitive substring filter on scope name.
            view: Variation view. ``active`` reads deployed; ``draft`` reads the latest builder
                snapshot.
            manager_id: Return only scopes supervised by this manager scope id.

        Returns:
            A page of scopes.

        Example:
            >>> for scope in mgmt.scopes.list().auto_paging_iter():
            ...     print(scope.id, scope.name, scope.status)
        """
        validate_page_size(page_size)
        return self._list_page(page_size, page_token, search, view, manager_id)

    def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        search: Optional[str],
        view: Optional[VariationView],
        manager_id: Optional[int],
    ) -> Page[Skill]:
        params = aip_list_params(page_size, page_token)
        if search is not None:
            params["search"] = search
        if view is not None:
            params["view"] = view
        if manager_id is not None:
            params["managerId"] = manager_id
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopesController_list",
                query=params,
            ),
            self._config.max_retries,
        )
        return build_aip_page_mapped(
            data,
            "scopes",
            Skill.model_validate,
            lambda cur: self._list_page(page_size, cur, search, view, manager_id),
        )

    def get(self, scope_id: Union[int, str], *, view: Optional[VariationView] = None) -> Skill:
        """
        Get a scope.

        Returns a scope. ``view=active`` (default) returns the deployed version; ``view=draft``
        returns the latest unpublished edits. Returns 404 if you cannot access the scope.

        **Requires:** ``scopes:read``

        Args:
            scope_id: Numeric scope id.
            view: Which variation snapshot to read. Defaults to ``active``.

        Example:
            >>> scope = mgmt.scopes.get("PLACEHOLDER_SCOPE_ID")
            >>> print(scope.name, scope.status)
        """
        validate_id(scope_id, name="scope_id")
        query: dict = {}
        if view is not None:
            query["view"] = view
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopesController_get",
                path_params={"id": scope_id},
                query=query,
            ),
            self._config.max_retries,
        )
        return Skill.model_validate(raw)

    def delete(self, scope_id: Union[int, str]) -> None:
        """
        Delete a scope.

        Deletes a scope. The scope can be restored later with POST /scopes/{id}/restore. Deleting an
        already-deleted scope is a no-op.

        **Requires:** ``scopes:write``

        Args:
            scope_id: Numeric scope id.

        Example:
            >>> mgmt = modus.management.ModusManagement()
            >>> mgmt.scopes.delete("PLACEHOLDER_SCOPE_ID")
        """
        validate_id(scope_id, name="scope_id")
        with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopesController_delete",
                path_params={"id": scope_id},
            ),
            self._config.max_retries,
        )

    def restore(self, scope_id: Union[int, str]) -> Skill:
        """
        Restore a deleted scope.

        Restores a previously deleted scope and returns it. Restoring a scope that is already active
        returns it unchanged.

        **Requires:** ``scopes:write``

        Args:
            scope_id: Numeric scope id.
        """
        validate_id(scope_id, name="scope_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopesController_restore",
                path_params={"id": scope_id},
                json_body={},
            ),
            self._config.max_retries,
        )
        return Skill.model_validate(raw)

    def cancel_ownership_transfer(self, scope_id: Union[int, str]) -> Skill:
        """
        Cancel ownership transfer.

        Cancels a pending ownership transfer. The current owner may cancel; the pending recipient
        may decline.

        **Requires:** ``scopes:write``

        Args:
            scope_id: Numeric scope id.
        """
        validate_id(scope_id, name="scope_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopesController_cancelOwnershipTransfer",
                path_params={"id": scope_id},
            ),
            self._config.max_retries,
        )
        return Skill.model_validate(raw)

    def accept_ownership_transfer(self, scope_id: Union[int, str]) -> Skill:
        """
        Accept ownership transfer.

        Accepts a pending ownership transfer. Only the pending recipient may invoke this action.

        **Requires:** ``scopes:write``

        Args:
            scope_id: Numeric scope id.
        """
        validate_id(scope_id, name="scope_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "ScopesController_acceptOwnershipTransfer",
                path_params={"id": scope_id},
                json_body={},
            ),
            self._config.max_retries,
        )
        return Skill.model_validate(raw)


class _AsyncScopesResourceBase:
    """Generated base for the management ``scopes`` resource."""

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list(
        self,
        *,
        page_size: int = 25,
        page_token: Optional[str] = None,
        search: Optional[str] = None,
        view: Optional[VariationView] = None,
        manager_id: Optional[int] = None,
    ) -> AsyncPage[Skill]:
        """
        List scopes.

        Returns a paginated page of scopes the caller can at least ``use``. Scopes the caller cannot
        see are filtered out. Pagination uses an opaque token returned in ``next_page_token``.

        **Requires:** ``scopes:read``

        Args:
            page_size: Items per page. Defaults to 25.
            page_token: Opaque page token from a previous response's ``next_page_token``. Omit for
                the first page.
            search: Case-insensitive substring filter on scope name.
            view: Variation view. ``active`` reads deployed; ``draft`` reads the latest builder
                snapshot.
            manager_id: Return only scopes supervised by this manager scope id.

        Returns:
            A page of scopes.
        """
        validate_page_size(page_size)
        return await self._list_page(page_size, page_token, search, view, manager_id)

    async def _list_page(
        self,
        page_size: int,
        page_token: Optional[str],
        search: Optional[str],
        view: Optional[VariationView],
        manager_id: Optional[int],
    ) -> AsyncPage[Skill]:
        params = aip_list_params(page_size, page_token)
        if search is not None:
            params["search"] = search
        if view is not None:
            params["view"] = view
        if manager_id is not None:
            params["managerId"] = manager_id
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopesController_list",
                query=params,
            ),
            self._config.max_retries,
        )
        return build_async_aip_page_mapped(
            data,
            "scopes",
            Skill.model_validate,
            lambda cur: self._list_page(page_size, cur, search, view, manager_id),
        )

    async def get(
        self,
        scope_id: Union[int, str],
        *,
        view: Optional[VariationView] = None,
    ) -> Skill:
        """
        Get a scope.

        Returns a scope. ``view=active`` (default) returns the deployed version; ``view=draft``
        returns the latest unpublished edits. Returns 404 if you cannot access the scope.

        **Requires:** ``scopes:read``

        Args:
            scope_id: Numeric scope id.
            view: Which variation snapshot to read. Defaults to ``active``.
        """
        validate_id(scope_id, name="scope_id")
        query: dict = {}
        if view is not None:
            query["view"] = view
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopesController_get",
                path_params={"id": scope_id},
                query=query,
            ),
            self._config.max_retries,
        )
        return Skill.model_validate(raw)

    async def delete(self, scope_id: Union[int, str]) -> None:
        """
        Delete a scope.

        Deletes a scope. The scope can be restored later with POST /scopes/{id}/restore. Deleting an
        already-deleted scope is a no-op.

        **Requires:** ``scopes:write``

        Args:
            scope_id: Numeric scope id.
        """
        validate_id(scope_id, name="scope_id")
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopesController_delete",
                path_params={"id": scope_id},
            ),
            self._config.max_retries,
        )

    async def restore(self, scope_id: Union[int, str]) -> Skill:
        """
        Restore a deleted scope.

        Restores a previously deleted scope and returns it. Restoring a scope that is already active
        returns it unchanged.

        **Requires:** ``scopes:write``

        Args:
            scope_id: Numeric scope id.
        """
        validate_id(scope_id, name="scope_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopesController_restore",
                path_params={"id": scope_id},
                json_body={},
            ),
            self._config.max_retries,
        )
        return Skill.model_validate(raw)

    async def cancel_ownership_transfer(self, scope_id: Union[int, str]) -> Skill:
        """
        Cancel ownership transfer.

        Cancels a pending ownership transfer. The current owner may cancel; the pending recipient
        may decline.

        **Requires:** ``scopes:write``

        Args:
            scope_id: Numeric scope id.
        """
        validate_id(scope_id, name="scope_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopesController_cancelOwnershipTransfer",
                path_params={"id": scope_id},
            ),
            self._config.max_retries,
        )
        return Skill.model_validate(raw)

    async def accept_ownership_transfer(self, scope_id: Union[int, str]) -> Skill:
        """
        Accept ownership transfer.

        Accepts a pending ownership transfer. Only the pending recipient may invoke this action.

        **Requires:** ``scopes:write``

        Args:
            scope_id: Numeric scope id.
        """
        validate_id(scope_id, name="scope_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "ScopesController_acceptOwnershipTransfer",
                path_params={"id": scope_id},
                json_body={},
            ),
            self._config.max_retries,
        )
        return Skill.model_validate(raw)
