"""Dashboards resource — draft tiles, filters and layout for modus.management."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence, Union

from pydantic import BaseModel

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id

from ...types.context_dashboards import (
    Dashboard,
    DashboardElementKind,
    DashboardElementLayout,
    DashboardElementPatch,
    DashboardElementResult,
    DashboardElementsList,
    DashboardLayoutElement,
)

ElementKindInput = Union[DashboardElementKind, str]
LayoutInput = Union[DashboardElementLayout, Mapping[str, int]]
PatchInput = Union[DashboardElementPatch, Mapping[str, Any]]
LayoutElementInput = Union[DashboardLayoutElement, Mapping[str, Any]]


def _wire(value: Union[BaseModel, Mapping[str, Any]]) -> Dict[str, Any]:
    """Serialize a typed value with API field names; plain mappings pass through.

    ``exclude_unset`` keeps explicit ``None`` values, which clear a setting.
    """
    if isinstance(value, BaseModel):
        return value.model_dump(by_alias=True, exclude_unset=True, mode="json")
    return dict(value)


def _create_body(
    expected_revision: int, kind: ElementKindInput, title: str, layout: LayoutInput
) -> Dict[str, Any]:
    return {
        "expectedRevision": expected_revision,
        "kind": kind.value if isinstance(kind, DashboardElementKind) else kind,
        "title": title,
        "layout": _wire(layout),
    }


def _update_body(expected_revision: int, patch: PatchInput) -> Dict[str, Any]:
    return {"expectedRevision": expected_revision, "patch": _wire(patch)}


def _layout_body(
    expected_revision: int, elements: Sequence[LayoutElementInput]
) -> Dict[str, Any]:
    return {
        "expectedRevision": expected_revision,
        "elements": [_wire(element) for element in elements],
    }


class DashboardElementsResource:
    """Tiles and filters on one dashboard draft.

    mgmt.context.dashboards.elements(dashboard_id).list()                → DashboardElementsList
    mgmt.context.dashboards.elements(dashboard_id).get(element_id)       → DashboardElementResult
    mgmt.context.dashboards.elements(dashboard_id).create(...)           → DashboardElementResult
    mgmt.context.dashboards.elements(dashboard_id).update(element_id, ...) → Dashboard
    """

    def __init__(self, http: HttpClient, config: ModusConfig, dashboard_id: str) -> None:
        self._http = http
        self._config = config
        self._dashboard_id = dashboard_id

    def list(self) -> DashboardElementsList:
        """List every tile and filter on the dashboard draft.

        Returns:
            Each element's id, kind, title and grid position, plus the current
            ``draft_revision`` to pass as ``expected_revision`` on the next change.

        Raises:
            NotFoundError: The dashboard does not exist or you cannot edit it.

        Example:
            >>> listed = mgmt.context.dashboards.elements("DASHBOARD_ID").list()
            >>> [element.id for element in listed.elements]
        """
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_listElements",
                path_params={"dashboardId": self._dashboard_id},
            ),
            self._config.max_retries,
        )
        return DashboardElementsList.model_validate(data)

    def get(self, element_id: str) -> DashboardElementResult:
        """Get the full draft settings of one tile or filter.

        Args:
            element_id: Id of the tile or filter, as returned by ``list()``.

        Returns:
            The element's settings and the current ``draft_revision``.

        Raises:
            NotFoundError: The dashboard or the element does not exist, or you cannot
                edit the dashboard.

        Example:
            >>> result = mgmt.context.dashboards.elements("DASHBOARD_ID").get("ELEMENT_ID")
            >>> result.element.title
        """
        validate_id(element_id, name="element_id")
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_getElement",
                path_params={"dashboardId": self._dashboard_id, "elementId": element_id},
            ),
            self._config.max_retries,
        )
        return DashboardElementResult.model_validate(data)

    def create(
        self,
        *,
        expected_revision: int,
        kind: ElementKindInput,
        title: str,
        layout: LayoutInput,
    ) -> DashboardElementResult:
        """Add a blank tile or filter to the dashboard draft.

        The new element gets its id from Modus; configure it afterwards with
        ``update()``.

        Args:
            expected_revision: The ``draft_revision`` your change is based on.
            kind: ``chart``, ``kpi``, ``table``, ``markdown`` or ``filter``.
            title: Title shown on the element.
            layout: Grid position with ``x`` (0-11), ``y``, ``w`` (1-12) and ``h``,
                as a ``DashboardElementLayout`` or a dict.

        Returns:
            The created element and the new ``draft_revision``.

        Raises:
            ConflictError: The draft changed since ``expected_revision``; list
                the elements again and retry with the new revision.
            ModusError: The position overlaps another element or a value is invalid.

        Example:
            >>> created = mgmt.context.dashboards.elements("DASHBOARD_ID").create(
            ...     expected_revision=3,
            ...     kind="chart",
            ...     title="Sales by region",
            ...     layout={"x": 0, "y": 4, "w": 6, "h": 4},
            ... )
            >>> created.element.id
        """
        body = _create_body(expected_revision, kind, title, layout)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_createElement",
                path_params={"dashboardId": self._dashboard_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return DashboardElementResult.model_validate(data)

    def update(
        self, element_id: str, *, expected_revision: int, patch: PatchInput
    ) -> Dashboard:
        """Change settings of one tile or filter on the dashboard draft.

        Args:
            element_id: Id of the tile or filter to change.
            expected_revision: The ``draft_revision`` your change is based on.
            patch: The settings to change, as a ``DashboardElementPatch`` or a
                dict keyed by API field names (for example ``{"title": "Sales"}``
                or ``{"defaultValue": None}``). Only the fields you set are sent;
                ``None`` clears a setting that supports clearing.

        Returns:
            The whole dashboard after the change, including the new ``draft_revision``.

        Raises:
            ConflictError: The draft changed since ``expected_revision``.
            NotFoundError: The dashboard or the element does not exist, or you cannot
                edit the dashboard.
            ModusError: The patch does not fit the element kind or a value is invalid.

        Example:
            >>> dashboard = mgmt.context.dashboards.elements("DASHBOARD_ID").update(
            ...     "ELEMENT_ID", expected_revision=3, patch={"title": "Revenue"}
            ... )
            >>> dashboard.draft_revision
        """
        validate_id(element_id, name="element_id")
        body = _update_body(expected_revision, patch)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_updateElement",
                path_params={"dashboardId": self._dashboard_id, "elementId": element_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(data)


class DashboardsResource:
    """Dashboards in the Modus knowledge base.

    mgmt.context.dashboards.elements(dashboard_id)            → DashboardElementsResource
    mgmt.context.dashboards.update_layout(dashboard_id, ...)  → Dashboard
    """

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def elements(self, dashboard_id: str) -> DashboardElementsResource:
        """Work with the tiles and filters of one dashboard draft.

        Args:
            dashboard_id: Id of the dashboard.

        Example:
            >>> mgmt.context.dashboards.elements("DASHBOARD_ID").list()
        """
        validate_id(dashboard_id, name="dashboard_id")
        return DashboardElementsResource(self._http, self._config, dashboard_id)

    def update_layout(
        self,
        dashboard_id: str,
        *,
        expected_revision: int,
        elements: Sequence[LayoutElementInput],
    ) -> Dashboard:
        """Move or resize several tiles and filters in one change.

        Args:
            dashboard_id: Id of the dashboard.
            expected_revision: The ``draft_revision`` your change is based on.
            elements: Every element to place, each with ``element_id`` and its
                final ``layout``, as ``DashboardLayoutElement`` values or dicts
                such as ``{"elementId": "...", "layout": {"x": 0, "y": 0, "w": 6, "h": 4}}``.

        Returns:
            The whole dashboard after the change, including the new ``draft_revision``.

        Raises:
            ConflictError: The draft changed since ``expected_revision``.
            ModusError: An element is unknown, positions overlap, or a value is invalid.

        Example:
            >>> mgmt.context.dashboards.update_layout(
            ...     "DASHBOARD_ID",
            ...     expected_revision=3,
            ...     elements=[{"elementId": "ELEMENT_ID", "layout": {"x": 0, "y": 0, "w": 12, "h": 2}}],
            ... )
        """
        validate_id(dashboard_id, name="dashboard_id")
        body = _layout_body(expected_revision, elements)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_updateLayout",
                path_params={"dashboardId": dashboard_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(data)


class AsyncDashboardElementsResource:
    """Async twin of ``DashboardElementsResource``."""

    def __init__(self, http: AsyncHttpClient, config: ModusConfig, dashboard_id: str) -> None:
        self._http = http
        self._config = config
        self._dashboard_id = dashboard_id

    async def list(self) -> DashboardElementsList:
        """List every tile and filter on the dashboard draft. See the sync ``list``."""
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_listElements",
                path_params={"dashboardId": self._dashboard_id},
            ),
            self._config.max_retries,
        )
        return DashboardElementsList.model_validate(data)

    async def get(self, element_id: str) -> DashboardElementResult:
        """Get the full draft settings of one tile or filter. See the sync ``get``."""
        validate_id(element_id, name="element_id")
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_getElement",
                path_params={"dashboardId": self._dashboard_id, "elementId": element_id},
            ),
            self._config.max_retries,
        )
        return DashboardElementResult.model_validate(data)

    async def create(
        self,
        *,
        expected_revision: int,
        kind: ElementKindInput,
        title: str,
        layout: LayoutInput,
    ) -> DashboardElementResult:
        """Add a blank tile or filter to the dashboard draft. See the sync ``create``."""
        body = _create_body(expected_revision, kind, title, layout)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_createElement",
                path_params={"dashboardId": self._dashboard_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return DashboardElementResult.model_validate(data)

    async def update(
        self, element_id: str, *, expected_revision: int, patch: PatchInput
    ) -> Dashboard:
        """Change settings of one tile or filter on the draft. See the sync ``update``."""
        validate_id(element_id, name="element_id")
        body = _update_body(expected_revision, patch)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_updateElement",
                path_params={"dashboardId": self._dashboard_id, "elementId": element_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(data)


class AsyncDashboardsResource:
    """Async twin of ``DashboardsResource``."""

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def elements(self, dashboard_id: str) -> AsyncDashboardElementsResource:
        """Work with the tiles and filters of one dashboard draft. See the sync ``elements``."""
        validate_id(dashboard_id, name="dashboard_id")
        return AsyncDashboardElementsResource(self._http, self._config, dashboard_id)

    async def update_layout(
        self,
        dashboard_id: str,
        *,
        expected_revision: int,
        elements: Sequence[LayoutElementInput],
    ) -> Dashboard:
        """Move or resize several tiles and filters in one change. See the sync ``update_layout``."""
        validate_id(dashboard_id, name="dashboard_id")
        body = _layout_body(expected_revision, elements)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_updateLayout",
                path_params={"dashboardId": dashboard_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(data)

