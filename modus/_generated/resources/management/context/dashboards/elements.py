# Auto-generated from the Modus API schema. Do not edit by hand.

from __future__ import annotations

from typing import Union

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._retry import async_with_retry, with_retry
from modus._validation import validate_id
from modus.management.types.context_dashboards import DashboardElementResult, DashboardElementsList


class _ContextDashboardsElementsResourceBase:
    """Generated base for the management ``context.dashboards.elements`` resource."""

    def __init__(
        self,
        http: HttpClient,
        config: ModusConfig,
        dashboard_id: Union[int, str],
    ) -> None:
        self._http = http
        self._config = config
        self._dashboard_id = dashboard_id

    def list(self) -> DashboardElementsList:
        """
        List dashboard elements.

        Lists every tile and filter on the dashboard draft with id, kind, title and layout. Filters
        also carry sqlReferences, the exact templates tile SQL must use to reference them. Returns
        the current draftRevision.

        **Requires:** ``context:read``

        Example:
            >>> listed = mgmt.context.dashboards.elements("DASHBOARD_ID").list()
            >>> [element.id for element in listed.elements]
        """
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_listElements",
                path_params={"dashboardId": self._dashboard_id},
            ),
            self._config.max_retries,
        )
        return DashboardElementsList.model_validate(raw)

    def get(self, element_id: str) -> DashboardElementResult:
        """
        Get a dashboard element.

        Returns the full draft configuration of one dashboard element, including SQL, chart settings
        and filter options, with the current draftRevision.

        **Requires:** ``context:read``

        Args:
            element_id: The dashboard element id to read.

        Example:
            >>> result = mgmt.context.dashboards.elements("DASHBOARD_ID").get("ELEMENT_ID")
            >>> result.element.title
        """
        validate_id(element_id, name="element_id")
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "DashboardsController_getElement",
                path_params={"dashboardId": self._dashboard_id, "elementId": element_id},
            ),
            self._config.max_retries,
        )
        return DashboardElementResult.model_validate(raw)


class _AsyncContextDashboardsElementsResourceBase:
    """Generated base for the management ``context.dashboards.elements`` resource."""

    def __init__(
        self,
        http: AsyncHttpClient,
        config: ModusConfig,
        dashboard_id: Union[int, str],
    ) -> None:
        self._http = http
        self._config = config
        self._dashboard_id = dashboard_id

    async def list(self) -> DashboardElementsList:
        """
        List dashboard elements.

        Lists every tile and filter on the dashboard draft with id, kind, title and layout. Filters
        also carry sqlReferences, the exact templates tile SQL must use to reference them. Returns
        the current draftRevision.

        **Requires:** ``context:read``
        """
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_listElements",
                path_params={"dashboardId": self._dashboard_id},
            ),
            self._config.max_retries,
        )
        return DashboardElementsList.model_validate(raw)

    async def get(self, element_id: str) -> DashboardElementResult:
        """
        Get a dashboard element.

        Returns the full draft configuration of one dashboard element, including SQL, chart settings
        and filter options, with the current draftRevision.

        **Requires:** ``context:read``

        Args:
            element_id: The dashboard element id to read.
        """
        validate_id(element_id, name="element_id")
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "DashboardsController_getElement",
                path_params={"dashboardId": self._dashboard_id, "elementId": element_id},
            ),
            self._config.max_retries,
        )
        return DashboardElementResult.model_validate(raw)
