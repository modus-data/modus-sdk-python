"""Immutable integration request and response uploads."""

from __future__ import annotations

from modus._config import ModusConfig
from modus._generated.models import CreatedIngestedDataResponseDto
from modus._http import AsyncHttpClient, HttpClient
from modus._openapi_invoke import invoke_operation, invoke_operation_async
from modus._retry import async_with_retry, with_retry
from modus.types.ingested_data import (
    IngestedDataRequest,
    IngestedDataResponse,
    IngestedDataUploadResult,
)


def _upload_body(
    *,
    integration_type: str,
    request: IngestedDataRequest,
    response: IngestedDataResponse,
) -> dict:
    return {
        "integration_type": integration_type,
        "request": request,
        "response": response,
    }


class IngestedDataResource:
    """Store exact integration requests and responses as immutable ingested data."""

    def __init__(self, http: HttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    def upload(
        self,
        *,
        integration_type: str,
        request: IngestedDataRequest,
        response: IngestedDataResponse,
    ) -> IngestedDataUploadResult:
        """Store a complete SQL or HTTP request and response exactly once.

        Identity covers the complete organization, integration, request, and
        response content while preserving every string exactly. A duplicate raises
        :class:`modus.ConflictError`, which means the identical payload is already
        stored and may be treated as a safe retry outcome.

        Args:
            integration_type: Canonical Modus integration identifier.
            request: Exact SQL or HTTP request that produced the response.
            response: Response format and exact string content. SQL requires CSV.

        Returns:
            The checksum and organization-scoped object key for the new upload.

        Raises:
            ConflictError: The complete payload is already stored.
            PermissionDeniedError: The token lacks ``context:write``.
            ModusError: The request shape or integration identifier is invalid
                (HTTP 400).

        Example:
            >>> client = modus.Modus()
            >>> stored = client.ingested_data.upload(
            ...     integration_type="snowflake",
            ...     request={"type": "sql", "query": "SELECT id, total FROM orders"},
            ...     response={"format": "csv", "content": "id,total\\n1,42.00\\n"},
            ... )
            >>> stored.checksum
        """
        data = with_retry(
            lambda: invoke_operation(
                self._http,
                "IngestedDataController_upload",
                json_body=_upload_body(
                    integration_type=integration_type,
                    request=request,
                    response=response,
                ),
            ),
            self._config.max_retries,
        )
        return CreatedIngestedDataResponseDto.model_validate(data)


class AsyncIngestedDataResource:
    """Asynchronous immutable ingested-data uploads."""

    def __init__(self, http: AsyncHttpClient, config: ModusConfig) -> None:
        self._http = http
        self._config = config

    async def upload(
        self,
        *,
        integration_type: str,
        request: IngestedDataRequest,
        response: IngestedDataResponse,
    ) -> IngestedDataUploadResult:
        """Store a complete request and response asynchronously.

        A :class:`modus.ConflictError` means the complete payload is already stored
        and may be treated as a safe retry outcome.

        Args:
            integration_type: Canonical Modus integration identifier.
            request: Exact SQL or HTTP request that produced the response.
            response: Response format and exact string content. SQL requires CSV.

        Returns:
            The checksum and organization-scoped object key for the new upload.

        Raises:
            ConflictError: The complete payload is already stored.
            PermissionDeniedError: The token lacks ``context:write``.
            ModusError: The request shape or integration identifier is invalid
                (HTTP 400).

        Example:
            >>> async_client = modus.AsyncModus()
            >>> stored = await async_client.ingested_data.upload(
            ...     integration_type="snowflake",
            ...     request={"type": "sql", "query": "SELECT 1"},
            ...     response={"format": "csv", "content": "value\\n1\\n"},
            ... )
            >>> stored.checksum
        """
        data = await async_with_retry(
            lambda: invoke_operation_async(
                self._http,
                "IngestedDataController_upload",
                json_body=_upload_body(
                    integration_type=integration_type,
                    request=request,
                    response=response,
                ),
            ),
            self._config.max_retries,
        )
        return CreatedIngestedDataResponseDto.model_validate(data)
