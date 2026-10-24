"""Usage metrics resource."""

from __future__ import annotations

from typing import Literal, Optional, Sequence

from modus._generated.resources.management.usage import (
    _AsyncUsageResourceBase,
    _UsageResourceBase,
)
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._retry import async_with_retry, with_retry

from ..types.usage import UsageReport

UsageRollup = Literal["hour", "day"]


class UsageResource(_UsageResourceBase):
    """Query organisation usage metrics."""

    def list(
        self,
        *,
        since: str,
        until: str,
        rollup: UsageRollup,
        model: Optional[str] = None,
        user_email: Optional[Sequence[str]] = None,
    ) -> UsageReport:
        """
        List usage metrics for your organisation over a time window.

        Args:
            since:      Start of the window (ISO 8601, inclusive).
            until:      End of the window (ISO 8601, exclusive).
            rollup:     Bucket size for each row (``hour`` or ``day``).
            model:      Optional filter to a single model name.
            user_email: Optional filter to one or more acting-user emails.

        Raises:
            UnprocessableError: The request was rejected by the API.
            AuthenticationError: Invalid or missing API key.
        """
        params: dict[str, object] = {"since": since, "until": until, "rollup": rollup}
        if model is not None:
            params["model"] = model
        if user_email is not None:
            params["user_email"] = list(user_email)
        data = with_retry(
            lambda: invoke_operation(self._http, "UsageController_list", query=params),
            self._config.max_retries,
        )
        return UsageReport.model_validate(data)


class AsyncUsageResource(_AsyncUsageResourceBase):
    async def list(
        self,
        *,
        since: str,
        until: str,
        rollup: UsageRollup,
        model: Optional[str] = None,
        user_email: Optional[Sequence[str]] = None,
    ) -> UsageReport:
        """
        List usage metrics for your organisation over a time window.

        Args:
            since:      Start of the window (ISO 8601, inclusive).
            until:      End of the window (ISO 8601, exclusive).
            rollup:     Bucket size for each row (``hour`` or ``day``).
            model:      Optional filter to a single model name.
            user_email: Optional filter to one or more acting-user emails.

        Raises:
            UnprocessableError: The request was rejected by the API.
            AuthenticationError: Invalid or missing API key.
        """
        params: dict[str, object] = {"since": since, "until": until, "rollup": rollup}
        if model is not None:
            params["model"] = model
        if user_email is not None:
            params["user_email"] = list(user_email)
        data = await async_with_retry(
            lambda: invoke_operation_async(self._http, "UsageController_list", query=params),
            self._config.max_retries,
        )
        return UsageReport.model_validate(data)
