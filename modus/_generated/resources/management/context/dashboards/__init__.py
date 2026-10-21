# Auto-generated from the Modus API schema. Do not edit by hand.

from __future__ import annotations

from typing import List

from modus._config import ModusConfig
from modus._generated.models import (
    ListDashboardDraftSnapshotsResponseDto,
    ListDashboardVersionsResponseDto,
)
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id
from modus.management.types.context_dashboards import (
    Dashboard,
    DashboardDraftSnapshot,
    DashboardVersion,
)


class _ContextDashboardsResourceBase:
    """Generated base for the management ``context.dashboards`` resource."""

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def delete(self, dashboard_id: str) -> None:
        """
        Delete a dashboard.

        Removes the dashboard from every listing and deletes its alert workflows. It cannot be
        restored through the API.

        **Requires:** ``context:write``

        Args:
            dashboard_id: Dashboard id, as shown in the app URL.

        Example:
            >>> mgmt.context.dashboards.delete("DASHBOARD_ID")
        """
        validate_id(dashboard_id, name="dashboard_id")
        with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_delete",
                path_params={"dashboardId": dashboard_id},
            ),
            self._config.max_retries,
        )

    def list_draft_snapshots(self, dashboard_id: str) -> List[DashboardDraftSnapshot]:
        """
        List dashboard draft snapshots.

        Returns ids and timestamps of the most recent draft snapshots. Editors only.

        **Requires:** ``context:read``

        Args:
            dashboard_id: Dashboard id, as shown in the app URL.

        Example:
            >>> snapshots = mgmt.context.dashboards.list_draft_snapshots("DASHBOARD_ID")
            >>> [s.uid for s in snapshots]
        """
        validate_id(dashboard_id, name="dashboard_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_listDraftSnapshots",
                path_params={"dashboardId": dashboard_id},
            ),
            self._config.max_retries,
        )
        return ListDashboardDraftSnapshotsResponseDto.model_validate(raw).snapshots

    def cancel_ownership_transfer(self, dashboard_id: str) -> Dashboard:
        """
        Cancel an ownership transfer.

        Owner only. Clears the pending transfer and returns the dashboard.

        **Requires:** ``context:write``

        Args:
            dashboard_id: Dashboard id, as shown in the app URL.

        Example:
            >>> mgmt.context.dashboards.cancel_ownership_transfer("DASHBOARD_ID")
        """
        validate_id(dashboard_id, name="dashboard_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_cancelOwnership",
                path_params={"dashboardId": dashboard_id},
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(raw)

    def accept_ownership_transfer(self, dashboard_id: str) -> Dashboard:
        """
        Accept an ownership transfer.

        Recipient only. Makes you the owner and clears the pending transfer.

        **Requires:** ``context:write``

        Args:
            dashboard_id: Dashboard id, as shown in the app URL.

        Example:
            >>> mgmt.context.dashboards.accept_ownership_transfer("DASHBOARD_ID")
        """
        validate_id(dashboard_id, name="dashboard_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_acceptOwnership",
                path_params={"dashboardId": dashboard_id},
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(raw)

    def list_versions(self, dashboard_id: str) -> List[DashboardVersion]:
        """
        List dashboard versions.

        Returns the published versions, newest first, each with its full definition. Draft snapshots
        are not included. The response is not paginated and can be large.

        **Requires:** ``context:read``

        Args:
            dashboard_id: Dashboard id, as shown in the app URL.

        Example:
            >>> versions = mgmt.context.dashboards.list_versions("DASHBOARD_ID")
            >>> [(v.uid, v.version_number) for v in versions]
        """
        validate_id(dashboard_id, name="dashboard_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_listVersions",
                path_params={"dashboardId": dashboard_id},
            ),
            self._config.max_retries,
        )
        return ListDashboardVersionsResponseDto.model_validate(raw).versions

    def get_version(self, dashboard_id: str, version_id: str) -> Dashboard:
        """
        Get a dashboard version.

        Returns the dashboard as it was in the given version. For a draft snapshot (editors only)
        the view is reported as active and selectedVersion.versionNumber is null.

        **Requires:** ``context:read``

        Args:
            dashboard_id: Dashboard id, as shown in the app URL.
            version_id: Version id, or a draft snapshot id for editors.

        Example:
            >>> old = mgmt.context.dashboards.get_version("DASHBOARD_ID", "VERSION_ID")
            >>> old.selected_version.version_number
        """
        validate_id(dashboard_id, name="dashboard_id")
        validate_id(version_id, name="version_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_getVersion",
                path_params={"dashboardId": dashboard_id, "versionId": version_id},
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(raw)

    def restore_version(self, dashboard_id: str, version_id: str) -> Dashboard:
        """
        Restore a dashboard version.

        Replaces the current draft with the content of the given version. The outgoing draft is kept
        as a draft snapshot. Returns the draft view.

        **Requires:** ``context:write``

        Args:
            dashboard_id: Dashboard id, as shown in the app URL.
            version_id: Version id, or a draft snapshot id for editors.

        Example:
            >>> mgmt.context.dashboards.restore_version("DASHBOARD_ID", "VERSION_ID")
        """
        validate_id(dashboard_id, name="dashboard_id")
        validate_id(version_id, name="version_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_restore",
                path_params={"dashboardId": dashboard_id, "versionId": version_id},
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(raw)


class _AsyncContextDashboardsResourceBase:
    """Generated base for the management ``context.dashboards`` resource."""

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def delete(self, dashboard_id: str) -> None:
        """
        Delete a dashboard.

        Removes the dashboard from every listing and deletes its alert workflows. It cannot be
        restored through the API.

        **Requires:** ``context:write``

        Args:
            dashboard_id: Dashboard id, as shown in the app URL.
        """
        validate_id(dashboard_id, name="dashboard_id")
        await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_delete",
                path_params={"dashboardId": dashboard_id},
            ),
            self._config.max_retries,
        )

    async def list_draft_snapshots(self, dashboard_id: str) -> List[DashboardDraftSnapshot]:
        """
        List dashboard draft snapshots.

        Returns ids and timestamps of the most recent draft snapshots. Editors only.

        **Requires:** ``context:read``

        Args:
            dashboard_id: Dashboard id, as shown in the app URL.
        """
        validate_id(dashboard_id, name="dashboard_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_listDraftSnapshots",
                path_params={"dashboardId": dashboard_id},
            ),
            self._config.max_retries,
        )
        return ListDashboardDraftSnapshotsResponseDto.model_validate(raw).snapshots

    async def cancel_ownership_transfer(self, dashboard_id: str) -> Dashboard:
        """
        Cancel an ownership transfer.

        Owner only. Clears the pending transfer and returns the dashboard.

        **Requires:** ``context:write``

        Args:
            dashboard_id: Dashboard id, as shown in the app URL.
        """
        validate_id(dashboard_id, name="dashboard_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_cancelOwnership",
                path_params={"dashboardId": dashboard_id},
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(raw)

    async def accept_ownership_transfer(self, dashboard_id: str) -> Dashboard:
        """
        Accept an ownership transfer.

        Recipient only. Makes you the owner and clears the pending transfer.

        **Requires:** ``context:write``

        Args:
            dashboard_id: Dashboard id, as shown in the app URL.
        """
        validate_id(dashboard_id, name="dashboard_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_acceptOwnership",
                path_params={"dashboardId": dashboard_id},
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(raw)

    async def list_versions(self, dashboard_id: str) -> List[DashboardVersion]:
        """
        List dashboard versions.

        Returns the published versions, newest first, each with its full definition. Draft snapshots
        are not included. The response is not paginated and can be large.

        **Requires:** ``context:read``

        Args:
            dashboard_id: Dashboard id, as shown in the app URL.
        """
        validate_id(dashboard_id, name="dashboard_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_listVersions",
                path_params={"dashboardId": dashboard_id},
            ),
            self._config.max_retries,
        )
        return ListDashboardVersionsResponseDto.model_validate(raw).versions

    async def get_version(self, dashboard_id: str, version_id: str) -> Dashboard:
        """
        Get a dashboard version.

        Returns the dashboard as it was in the given version. For a draft snapshot (editors only)
        the view is reported as active and selectedVersion.versionNumber is null.

        **Requires:** ``context:read``

        Args:
            dashboard_id: Dashboard id, as shown in the app URL.
            version_id: Version id, or a draft snapshot id for editors.
        """
        validate_id(dashboard_id, name="dashboard_id")
        validate_id(version_id, name="version_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_getVersion",
                path_params={"dashboardId": dashboard_id, "versionId": version_id},
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(raw)

    async def restore_version(self, dashboard_id: str, version_id: str) -> Dashboard:
        """
        Restore a dashboard version.

        Replaces the current draft with the content of the given version. The outgoing draft is kept
        as a draft snapshot. Returns the draft view.

        **Requires:** ``context:write``

        Args:
            dashboard_id: Dashboard id, as shown in the app URL.
            version_id: Version id, or a draft snapshot id for editors.
        """
        validate_id(dashboard_id, name="dashboard_id")
        validate_id(version_id, name="version_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_restore",
                path_params={"dashboardId": dashboard_id, "versionId": version_id},
            ),
            self._config.max_retries,
        )
        return Dashboard.model_validate(raw)
