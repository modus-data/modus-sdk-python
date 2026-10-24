# Auto-generated from the Modus API schema. Do not edit by hand.

from __future__ import annotations

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._retry import async_with_retry, with_retry
from modus.management.types.usage import UsageUsersReport


class _UsageResourceBase:
    """Generated base for the management ``usage`` resource."""

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list_users(self, *, since: str, until: str) -> UsageUsersReport:
        """
        List usage users.

        Returns the distinct acting-user emails that appear in your organization's LLM usage over
        the ``[since, until)`` window. Feeds the usage page's user filter (includes non-Modus
        Slack/Teams users). Scoped to your organization.

        **Requires:** ``usage:read``

        Args:
            since: ISO8601 start of the query window (inclusive).
            until: ISO8601 end of the query window (exclusive).
        """
        query: dict = {"since": since, "until": until}
        raw = with_retry(
            lambda: invoke_operation(
                self._http,
                "UsageController_listUsers",
                query=query,
            ),
            self._config.max_retries,
        )
        return UsageUsersReport.model_validate(raw)


class _AsyncUsageResourceBase:
    """Generated base for the management ``usage`` resource."""

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list_users(self, *, since: str, until: str) -> UsageUsersReport:
        """
        List usage users.

        Returns the distinct acting-user emails that appear in your organization's LLM usage over
        the ``[since, until)`` window. Feeds the usage page's user filter (includes non-Modus
        Slack/Teams users). Scoped to your organization.

        **Requires:** ``usage:read``

        Args:
            since: ISO8601 start of the query window (inclusive).
            until: ISO8601 end of the query window (exclusive).
        """
        query: dict = {"since": since, "until": until}
        raw = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "UsageController_listUsers",
                query=query,
            ),
            self._config.max_retries,
        )
        return UsageUsersReport.model_validate(raw)
