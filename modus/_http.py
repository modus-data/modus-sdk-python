"""
HTTP transport layer.

HttpClient and AsyncHttpClient are thin wrappers around httpx that handle:
  - Auth header injection (via ModusConfig)
  - Response parsing (JSON or None for 204)
  - HTTP status code → typed exception mapping
  - Raw SSE line streaming (for skill execution)

Retry logic lives in _retry.py and is applied at the resource layer,
not here. This keeps each layer's responsibility clear.
"""

from __future__ import annotations
import json
from typing import Any, AsyncIterator, Dict, Iterator, Optional
import platform

import httpx
from importlib.metadata import PackageNotFoundError, version

from ._auth import auth_headers
from ._config import ModusConfig
from ._exceptions import (
    APIConnectionError,
    AuthenticationError,
    ConflictError,
    InternalServerError,
    ModusError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableError,
)

try:
    _SDK_VERSION = version("modus")
except PackageNotFoundError:
    _SDK_VERSION = "0.0.0+dev"

_USER_AGENT = (
    f"modus-python/{_SDK_VERSION} "
    f"(python/{platform.python_version()}; {platform.system().lower()})"
)


_NETWORK_ERRORS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.RemoteProtocolError,
)


def _wrap_network_error(exc: Exception, base_url: str) -> APIConnectionError:
    """Convert any network-level httpx error into a typed APIConnectionError."""
    return APIConnectionError(
        f"Network error communicating with Modus API at {base_url!r}: {exc}. "
        "Check connectivity and that base_url is correct."
    )


# ---------------------------------------------------------------------------
# Error mapping
# ---------------------------------------------------------------------------


def _extract_message(response: httpx.Response) -> str:
    """Pull a human-readable message out of a NestJS error response body."""
    try:
        body = response.json()
        if isinstance(body, dict):
            # NestJS standard: { message: "..." } or { message: [...] }
            msg = body.get("message") or body.get("error")
            if isinstance(msg, list):
                return "; ".join(str(m) for m in msg)
            if msg:
                return str(msg)
    except (json.JSONDecodeError, ValueError):
        pass
    return response.text or f"HTTP {response.status_code}"


def _raise_for_status(response: httpx.Response) -> None:
    """Map an HTTP error response to the appropriate ModusError subclass."""
    if response.is_success:
        return

    message = _extract_message(response)
    status = response.status_code
    request_id = response.headers.get("x-request-id") or response.headers.get("X-Request-ID")
    headers = dict(response.headers)
    try:
        body = response.text
    except Exception:
        body = None

    kwargs: dict = dict(request_id=request_id, response_headers=headers, body=body)

    if status == 401:
        raise AuthenticationError(message, **kwargs)
    if status == 403:
        raise PermissionDeniedError(message, **kwargs)
    if status == 404:
        raise NotFoundError(message, **kwargs)
    if status == 409:
        raise ConflictError(message, **kwargs)
    if status == 422:
        try:
            errors = response.json()
        except (json.JSONDecodeError, ValueError):
            errors = None
        raise UnprocessableError(message, errors=errors, **kwargs)
    if status == 429:
        retry_after: Optional[int] = None
        header = response.headers.get("retry-after", "")
        if header.isdigit():
            retry_after = int(header)
        raise RateLimitError(message, retry_after=retry_after, **kwargs)
    if status >= 500:
        raise InternalServerError(message, status_code=status, **kwargs)

    raise ModusError(message, status_code=status, **kwargs)


# ---------------------------------------------------------------------------
# Sync client
# ---------------------------------------------------------------------------


class HttpClient:
    """
    Synchronous HTTP client. One instance per Modus client.

    All methods raise a ModusError subclass on HTTP error status.
    Retry logic is NOT here — resources apply with_retry() around calls.
    """

    def __init__(self, config: ModusConfig) -> None:
        self._config = config
        self._client = httpx.Client(
            base_url=config.base_url,
            headers={
                **auth_headers(config.api_key),
                "Accept": "application/json",
                "User-Agent": _USER_AGENT,
            },
            timeout=config.timeout,
        )

    def get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
        try:
            response = self._client.get(path, params=params)
        except _NETWORK_ERRORS as exc:
            raise _wrap_network_error(exc, self._config.base_url) from exc
        _raise_for_status(response)
        return response.json()

    def post(self, path: str, *, json: Optional[Dict[str, Any]] = None) -> Any:
        try:
            response = self._client.post(path, json=json)
        except _NETWORK_ERRORS as exc:
            raise _wrap_network_error(exc, self._config.base_url) from exc
        _raise_for_status(response)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def patch(self, path: str, *, json: Optional[Dict[str, Any]] = None) -> Any:
        try:
            response = self._client.patch(path, json=json)
        except _NETWORK_ERRORS as exc:
            raise _wrap_network_error(exc, self._config.base_url) from exc
        _raise_for_status(response)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def delete(self, path: str) -> Optional[Any]:
        try:
            response = self._client.delete(path)
        except _NETWORK_ERRORS as exc:
            raise _wrap_network_error(exc, self._config.base_url) from exc
        _raise_for_status(response)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def stream_post(
        self, path: str, *, json: Optional[Dict[str, Any]] = None
    ) -> Iterator[str]:
        """
        Make a streaming POST and yield raw SSE lines.

        The caller is responsible for parsing SSE syntax.
        """
        try:
            with self._client.stream("POST", path, json=json) as response:
                _raise_for_status(response)
                for line in response.iter_lines():
                    if line.strip():
                        yield line
        except _NETWORK_ERRORS as exc:
            raise _wrap_network_error(exc, self._config.base_url) from exc

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Async client
# ---------------------------------------------------------------------------


class AsyncHttpClient:
    """
    Asynchronous HTTP client. Mirrors HttpClient exactly with async/await.
    One instance per AsyncModus client.
    """

    def __init__(self, config: ModusConfig) -> None:
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            headers={
                **auth_headers(config.api_key),
                "Accept": "application/json",
                "User-Agent": _USER_AGENT,
            },
            timeout=config.timeout,
        )

    async def get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
        try:
            response = await self._client.get(path, params=params)
        except _NETWORK_ERRORS as exc:
            raise _wrap_network_error(exc, self._config.base_url) from exc
        _raise_for_status(response)
        return response.json()

    async def post(self, path: str, *, json: Optional[Dict[str, Any]] = None) -> Any:
        try:
            response = await self._client.post(path, json=json)
        except _NETWORK_ERRORS as exc:
            raise _wrap_network_error(exc, self._config.base_url) from exc
        _raise_for_status(response)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    async def patch(self, path: str, *, json: Optional[Dict[str, Any]] = None) -> Any:
        try:
            response = await self._client.patch(path, json=json)
        except _NETWORK_ERRORS as exc:
            raise _wrap_network_error(exc, self._config.base_url) from exc
        _raise_for_status(response)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    async def delete(self, path: str) -> Optional[Any]:
        try:
            response = await self._client.delete(path)
        except _NETWORK_ERRORS as exc:
            raise _wrap_network_error(exc, self._config.base_url) from exc
        _raise_for_status(response)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    async def stream_post(
        self, path: str, *, json: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """Streaming POST — yields raw SSE lines."""
        try:
            async with self._client.stream("POST", path, json=json) as response:
                _raise_for_status(response)
                async for line in response.aiter_lines():
                    if line.strip():
                        yield line
        except _NETWORK_ERRORS as exc:
            raise _wrap_network_error(exc, self._config.base_url) from exc

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncHttpClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
