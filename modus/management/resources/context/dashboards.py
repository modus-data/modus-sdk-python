"""Dashboards resource — documents, versions, access, draft tiles, filters and layout for modus.management."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

from pydantic import BaseModel

from modus._config import ModusConfig
from modus._generated.resources.management.context.dashboards import (
    _AsyncContextDashboardsResourceBase,
    _ContextDashboardsResourceBase,
)
from modus._generated.resources.management.context.dashboards.elements import (
    _AsyncContextDashboardsElementsResourceBase,
    _ContextDashboardsElementsResourceBase,
)
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id

from ...types.context_dashboards import (
    Dashboard,
    DashboardAccess,
    DashboardDefinition,
    DashboardElementKind,
    DashboardElementLayout,
    DashboardElementPatch,
    DashboardElementResult,
    DashboardGroupPermission,
    DashboardLayoutElement,
    DashboardPublishResult,
    DashboardSharedUser,
    DashboardView,
    DashboardVisibility,
)

ElementKindInput = Union[DashboardElementKind, str]
LayoutInput = Union[DashboardElementLayout, Mapping[str, int]]
PatchInput = Union[DashboardElementPatch, Mapping[str, Any]]
LayoutElementInput = Union[DashboardLayoutElement, Mapping[str, Any]]
ViewInput = Union[DashboardView, str]
DefinitionInput = Union[DashboardDefinition, Mapping[str, Any]]
AccessInput = Union[DashboardAccess, Mapping[str, Any]]
VisibilityInput = Union[DashboardVisibility, str]
GroupPermissionInput = Union[DashboardGroupPermission, Mapping[str, bool]]
SharedUserInput = Union[DashboardSharedUser, Mapping[str, Any]]


def _wire(value: Union[BaseModel, Mapping[str, Any]]) -> Dict[str, Any]:
    """Serialize a typed value with API field names; plain mappings pass through.

    ``exclude_unset`` keeps explicit ``None`` values, which clear a setting.
    """
    if isinstance(value, BaseModel):
        return value.model_dump(by_alias=True, exclude_unset=True, mode="json")
    return dict(value)


def _enum_value(value: Union[str, Enum]) -> str:
    return str(value.value) if isinstance(value, Enum) else value


def _omit_none(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _create_body(
    expected_revision: int, kind: ElementKindInput, title: str, layout: LayoutInput
) -> Dict[str, Any]:
    return {
        "expectedRevision": expected_revision,
        "kind": _enum_value(kind),
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


def _view_query(view: Optional[ViewInput]) -> Optional[Dict[str, Any]]:
    if view is None:
        return None
    return {"view": _enum_value(view)}


def _document_create_body(
    title: str,
    definition: DefinitionInput,
    description: Optional[str],
    access: Optional[AccessInput],
) -> Dict[str, Any]:
    return _omit_none(
        {
            "title": title,
            "definition": _wire(definition),
            "description": description,
            "access": _wire(access) if access is not None else None,
        }
    )


def _draft_body(
    expected_revision: int,
    definition: DefinitionInput,
    title: Optional[str],
    description: Optional[str],
) -> Dict[str, Any]:
    return _omit_none(
        {
            "expectedRevision": expected_revision,
            "definition": _wire(definition),
            "title": title,
            "description": description,
        }
    )


def _access_body(
    visibility: VisibilityInput,
    group_permissions: Mapping[str, GroupPermissionInput],
    shared_with: Sequence[SharedUserInput],
) -> Dict[str, Any]:
    return {
        "visibility": _enum_value(visibility),
        "groupPermissions": {
            group_id: _wire(permission) for group_id, permission in group_permissions.items()
        },
        "sharedWith": [_wire(user) for user in shared_with],
    }


class DashboardElementsResource(_ContextDashboardsElementsResourceBase):
    """Tiles and filters on one dashboard draft.

    mgmt.context.dashboards.elements(dashboard_id).list()                → DashboardElementsList
    mgmt.context.dashboards.elements(dashboard_id).get(element_id)       → DashboardElementResult
    mgmt.context.dashboards.elements(dashboard_id).create(...)           → DashboardElementResult
    mgmt.context.dashboards.elements(dashboard_id).update(element_id, ...) → Dashboard
    """

    def __init__(self, http: HttpClient, config: ModusConfig, dashboard_id: str) -> None:
        super().__init__(http, config, dashboard_id)

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


class DashboardsResource(_ContextDashboardsResourceBase):
    """Dashboards in the Modus knowledge base.

    mgmt.context.dashboards.list(view=...)                                → list[Dashboard]
    mgmt.context.dashboards.get(dashboard_id, view=...)                   → Dashboard
    mgmt.context.dashboards.create(title=..., definition=...)             → Dashboard
    mgmt.context.dashboards.update_draft(dashboard_id, ...)               → Dashboard
    mgmt.context.dashboards.publish(dashboard_id, expected_revision=...)  → DashboardPublishResult
    mgmt.context.dashboards.delete(dashboard_id)                          → None
    mgmt.context.dashboards.list_versions(dashboard_id)                   → list[DashboardVersion]
    mgmt.context.dashboards.get_version(dashboard_id, version_id)         → Dashboard
    mgmt.context.dashboards.restore_version(dashboard_id, version_id)     → Dashboard
    mgmt.context.dashboards.list_draft_snapshots(dashboard_id)            → list[DashboardDraftSnapshot]
    mgmt.context.dashboards.update_access(dashboard_id, ...)              → Dashboard
    mgmt.context.dashboards.request_ownership_transfer(dashboard_id, ...) → Dashboard
    mgmt.context.dashboards.accept_ownership_transfer(dashboard_id)       → Dashboard
    mgmt.context.dashboards.cancel_ownership_transfer(dashboard_id)       → Dashboard
    mgmt.context.dashboards.elements(dashboard_id)                        → DashboardElementsResource
    mgmt.context.dashboards.update_layout(dashboard_id, ...)              → Dashboard
    """

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        super().__init__(http, config)

    def list(self, *, view: Optional[ViewInput] = None) -> List[Dashboard]:
        """List dashboards with their full definitions.

        Args:
            view: ``active`` (default) lists published dashboards you can open;
                ``draft`` lists the drafts of dashboards you can edit.

        Returns:
            Every matching dashboard. The list is not paginated.

        Example:
            >>> drafts = mgmt.context.dashboards.list(view="draft")
            >>> [(d.id, d.title, d.draft_revision) for d in drafts]
        """
        query = _view_query(view)
        data = with_retry(
            lambda: invoke_operation(self._http, "DashboardsController_list", query=query),
            self._config.max_retries,
        )
        return [Dashboard.model_validate(item) for item in data["dashboards"]]

    def get(self, dashboard_id: str, *, view: Optional[ViewInput] = None) -> Dashboard:
        """Get one dashboard with its full definition.

        Args:
            dashboard_id: Id of the dashboard.
            view: ``active`` (default) returns the published version; ``draft``
                returns the working draft and requires edit access.

        Returns:
            The dashboard, including ``draft_revision`` for the next change.

        Raises:
            NotFoundError: The dashboard does not exist or you cannot open it.

        Example:
            >>> draft = mgmt.context.dashboards.get("DASHBOARD_ID", view="draft")
            >>> draft.draft_revision
        """
        validate_id(dashboard_id, name="dashboard_id")
        query = _view_query(view)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_get",
                path_params={"dashboardId": dashboard_id},
                query=query,
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(data)

    def create(
        self,
        *,
        title: str,
        definition: DefinitionInput,
        description: Optional[str] = None,
        access: Optional[AccessInput] = None,
    ) -> Dashboard:
        """Create a dashboard draft.

        The new dashboard is not visible to others until you ``publish()`` it.

        Args:
            title: Dashboard title.
            definition: Tiles, filters and layout, as a ``DashboardDefinition``
                or a dict such as ``{"tiles": [], "filters": []}``. Element ids
                must be unique.
            description: Optional dashboard description.
            access: Optional access settings, as a ``DashboardAccess`` or a dict
                with ``visibility``, ``groupPermissions`` and ``sharedWith``.
                Defaults to private.

        Returns:
            The created dashboard in its draft view.

        Raises:
            ModusError: The definition or access settings are invalid.

        Example:
            >>> dashboard = mgmt.context.dashboards.create(
            ...     title="Revenue", definition={"tiles": [], "filters": []}
            ... )
            >>> dashboard.id
        """
        body = _document_create_body(title, definition, description, access)
        data = with_retry(
            lambda: invoke_operation(self._http, "DashboardsController_create", json_body=body),
            self._config.max_retries,
        )
        return Dashboard.model_validate(data)

    def update_draft(
        self,
        dashboard_id: str,
        *,
        expected_revision: int,
        definition: DefinitionInput,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dashboard:
        """Replace the whole draft definition, and optionally the title and description.

        Args:
            dashboard_id: Id of the dashboard.
            expected_revision: The ``draft_revision`` your change is based on.
            definition: The complete new definition, as a ``DashboardDefinition``
                or a dict. Tiles and filters left out are removed.
            title: New title; unchanged when omitted.
            description: New description; unchanged when omitted.

        Returns:
            The dashboard draft after the change, including the new ``draft_revision``.

        Raises:
            ConflictError: The draft changed since ``expected_revision``; get the
                draft again and retry with the new revision.
            NotFoundError: The dashboard does not exist or you cannot edit it.
            ModusError: The definition is invalid.

        Example:
            >>> draft = mgmt.context.dashboards.get("DASHBOARD_ID", view="draft")
            >>> definition = draft.definition.model_dump(by_alias=True, exclude_unset=True)
            >>> mgmt.context.dashboards.update_draft(
            ...     "DASHBOARD_ID", expected_revision=draft.draft_revision, definition=definition
            ... )
        """
        validate_id(dashboard_id, name="dashboard_id")
        body = _draft_body(expected_revision, definition, title, description)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_updateDraft",
                path_params={"dashboardId": dashboard_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(data)

    def publish(self, dashboard_id: str, *, expected_revision: int) -> DashboardPublishResult:
        """Publish the draft as a new version that everyone with access sees.

        Alert workflows defined on the dashboard are updated to match.

        Args:
            dashboard_id: Id of the dashboard.
            expected_revision: The ``draft_revision`` you reviewed and want to publish.

        Returns:
            The published ``dashboard`` and the new ``version``.

        Raises:
            ConflictError: The draft changed since ``expected_revision``.
            NotFoundError: The dashboard does not exist or you cannot edit it.

        Example:
            >>> result = mgmt.context.dashboards.publish("DASHBOARD_ID", expected_revision=4)
            >>> result.version.version_number
        """
        validate_id(dashboard_id, name="dashboard_id")
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_publish",
                path_params={"dashboardId": dashboard_id},
                json_body={"expectedRevision": expected_revision},
            ),
            self._config.max_retries,
        )
        return DashboardPublishResult.model_validate(data)

    def update_access(
        self,
        dashboard_id: str,
        *,
        visibility: VisibilityInput,
        group_permissions: Mapping[str, GroupPermissionInput],
        shared_with: Sequence[SharedUserInput],
    ) -> Dashboard:
        """Replace who can open and edit a dashboard.

        All three settings are required and replace the current ones.

        Args:
            dashboard_id: Id of the dashboard.
            visibility: ``shared`` (the owner plus the groups in ``group_permissions``)
                or ``private`` (the owner plus the users in ``shared_with``).
            group_permissions: Group id to ``DashboardGroupPermission`` or a dict
                such as ``{"use": True, "manage": False}``. Used only when shared.
            shared_with: Users as ``DashboardSharedUser`` values or dicts such as
                ``{"email": "ana@example.com", "permission": "use"}``. Used only
                when private.

        Returns:
            The dashboard with its new access settings.

        Raises:
            NotFoundError: The dashboard does not exist or you cannot edit it.
            ModusError: A group, user or permission is invalid.

        Example:
            >>> mgmt.context.dashboards.update_access(
            ...     "DASHBOARD_ID",
            ...     visibility="private",
            ...     group_permissions={},
            ...     shared_with=[{"email": "ana@example.com", "permission": "use"}],
            ... )
        """
        validate_id(dashboard_id, name="dashboard_id")
        body = _access_body(visibility, group_permissions, shared_with)
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_updateAccess",
                path_params={"dashboardId": dashboard_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(data)

    def request_ownership_transfer(self, dashboard_id: str, new_owner_user_id: str) -> Dashboard:
        """Ask another member of your organization to take ownership of a dashboard.

        Only the owner can request a transfer. Ownership moves when the recipient
        calls ``accept_ownership_transfer()``.

        Args:
            dashboard_id: Id of the dashboard.
            new_owner_user_id: User id of the member who should become the owner.

        Returns:
            The dashboard with ``pending_ownership_transfer`` set.

        Raises:
            PermissionDeniedError: You are not the owner.
            NotFoundError: The dashboard does not exist or you cannot open it.

        Example:
            >>> mgmt.context.dashboards.request_ownership_transfer("DASHBOARD_ID", "USER_ID")
        """
        validate_id(dashboard_id, name="dashboard_id")
        validate_id(new_owner_user_id, name="new_owner_user_id")
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_transferOwnership",
                path_params={"dashboardId": dashboard_id},
                json_body={"newOwnerUserId": new_owner_user_id},
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(data)

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


class AsyncDashboardElementsResource(_AsyncContextDashboardsElementsResourceBase):
    """Async twin of ``DashboardElementsResource``."""

    def __init__(self, http: AsyncHttpClient, config: ModusConfig, dashboard_id: str) -> None:
        super().__init__(http, config, dashboard_id)

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


class AsyncDashboardsResource(_AsyncContextDashboardsResourceBase):
    """Async twin of ``DashboardsResource``."""

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        super().__init__(http, config)

    async def list(self, *, view: Optional[ViewInput] = None) -> List[Dashboard]:
        """List dashboards with their full definitions. See the sync ``list``."""
        query = _view_query(view)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, "DashboardsController_list", query=query
            ),
            self._config.max_retries,
        )
        return [Dashboard.model_validate(item) for item in data["dashboards"]]

    async def get(self, dashboard_id: str, *, view: Optional[ViewInput] = None) -> Dashboard:
        """Get one dashboard with its full definition. See the sync ``get``."""
        validate_id(dashboard_id, name="dashboard_id")
        query = _view_query(view)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_get",
                path_params={"dashboardId": dashboard_id},
                query=query,
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(data)

    async def create(
        self,
        *,
        title: str,
        definition: DefinitionInput,
        description: Optional[str] = None,
        access: Optional[AccessInput] = None,
    ) -> Dashboard:
        """Create a dashboard draft. See the sync ``create``."""
        body = _document_create_body(title, definition, description, access)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http, "DashboardsController_create", json_body=body
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(data)

    async def update_draft(
        self,
        dashboard_id: str,
        *,
        expected_revision: int,
        definition: DefinitionInput,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dashboard:
        """Replace the whole draft definition. See the sync ``update_draft``."""
        validate_id(dashboard_id, name="dashboard_id")
        body = _draft_body(expected_revision, definition, title, description)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_updateDraft",
                path_params={"dashboardId": dashboard_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(data)

    async def publish(
        self, dashboard_id: str, *, expected_revision: int
    ) -> DashboardPublishResult:
        """Publish the draft as a new version. See the sync ``publish``."""
        validate_id(dashboard_id, name="dashboard_id")
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_publish",
                path_params={"dashboardId": dashboard_id},
                json_body={"expectedRevision": expected_revision},
            ),
            self._config.max_retries,
        )
        return DashboardPublishResult.model_validate(data)

    async def update_access(
        self,
        dashboard_id: str,
        *,
        visibility: VisibilityInput,
        group_permissions: Mapping[str, GroupPermissionInput],
        shared_with: Sequence[SharedUserInput],
    ) -> Dashboard:
        """Replace who can open and edit a dashboard. See the sync ``update_access``."""
        validate_id(dashboard_id, name="dashboard_id")
        body = _access_body(visibility, group_permissions, shared_with)
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_updateAccess",
                path_params={"dashboardId": dashboard_id},
                json_body=body,
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(data)

    async def request_ownership_transfer(
        self, dashboard_id: str, new_owner_user_id: str
    ) -> Dashboard:
        """Ask a member to take ownership. See the sync ``request_ownership_transfer``."""
        validate_id(dashboard_id, name="dashboard_id")
        validate_id(new_owner_user_id, name="new_owner_user_id")
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_transferOwnership",
                path_params={"dashboardId": dashboard_id},
                json_body={"newOwnerUserId": new_owner_user_id},
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(data)

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
