"""Organisation administration resource."""

from __future__ import annotations

from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus._retry import async_with_retry, with_retry


class OrganizationResource:
    """Manage organisation-level settings."""

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def delete(self) -> None:
        """
        Permanently delete your Modus organisation.

        Raises:
            PermissionDeniedError: The API key lacks permission for this action.
            AuthenticationError: Invalid or missing API key.
        """
        with_retry(
            lambda: self._http.delete("/api/v1/users/organization"),
            self._config.max_retries,
        )


class AsyncOrganizationResource:
    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def delete(self) -> None:
        """
        Permanently delete your Modus organisation.

        Raises:
            PermissionDeniedError: The API key lacks permission for this action.
            AuthenticationError: Invalid or missing API key.
        """
        await async_with_retry(
            lambda: self._http.delete("/api/v1/users/organization"),
            self._config.max_retries,
        )
