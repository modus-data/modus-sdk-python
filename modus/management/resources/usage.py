"""Usage metrics resource."""

from __future__ import annotations

from typing import Literal, Optional

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._retry import async_with_retry, with_retry

from ..types.usage import UsageReport

UsageRollup = Literal["hour", "day"]


class UsageResource:
    """Query organisation usage metrics."""

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def list(
        self,
        *,
        since: str,
        until: str,
        rollup: UsageRollup,
        model: Optional[str] = None,
    ) -> UsageReport:
        """
        List usage metrics for your organisation over a time window.

        Args:
            since:  Start of the window (ISO 8601, inclusive).
            until:  End of the window (ISO 8601, exclusive).
            rollup: Bucket size for each row (``hour`` or ``day``).
            model:  Optional filter to a single model name.

        Raises:
            UnprocessableError: The request was rejected by the API.
            AuthenticationError: Invalid or missing API key.
        """
        params: dict[str, str] = {"since": since, "until": until, "rollup": rollup}
        if model is not None:
            params["model"] = model
        data = with_retry(
            lambda: self._http.get("/api/v1/usage", params=params),
            self._config.max_retries,
        )
        return UsageReport.model_validate(data)


class AsyncUsageResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def list(
        self,
        *,
        since: str,
        until: str,
        rollup: UsageRollup,
        model: Optional[str] = None,
    ) -> UsageReport:
        """
        List usage metrics for your organisation over a time window.

        Args:
            since:  Start of the window (ISO 8601, inclusive).
            until:  End of the window (ISO 8601, exclusive).
            rollup: Bucket size for each row (``hour`` or ``day``).
            model:  Optional filter to a single model name.

        Raises:
            UnprocessableError: The request was rejected by the API.
            AuthenticationError: Invalid or missing API key.
        """
        params: dict[str, str] = {"since": since, "until": until, "rollup": rollup}
        if model is not None:
            params["model"] = model
        data = await async_with_retry(
            lambda: self._http.get("/api/v1/usage", params=params),
            self._config.max_retries,
        )
        return UsageReport.model_validate(data)
