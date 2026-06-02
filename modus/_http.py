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
import platform
from importlib.metadata import PackageNotFoundError, version
from typing import Any, AsyncIterator, Dict, Iterator, Optional

import httpx

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


def _read_response_bytes(response: httpx.Response) -> bytes:
    """Return the full response body, including for unread streaming responses."""
    try:
        return response.content
    except httpx.ResponseNotRead:
        return response.read()


async def _read_response_bytes_async(response: httpx.Response) -> bytes:
    """Async variant for streaming responses from AsyncHttpClient."""
    try:
        return response.content
    except httpx.ResponseNotRead:
        return await response.aread()


def _message_from_body(raw: str, status_code: int) -> str:
    if not raw:
        return f"HTTP {status_code}"
    try:
        body = json.loads(raw)
        if isinstance(body, dict):
            msg = body.get("message") or body.get("error")
            if isinstance(msg, list):
                return "; ".join(str(m) for m in msg)
            if msg:
                return str(msg)
    except json.JSONDecodeError:
        pass
    return raw


def _extract_message(response: httpx.Response) -> str:
    """Pull a human-readable message out of a NestJS error response body."""
    raw_bytes = _read_response_bytes(response)
    raw = raw_bytes.decode(response.encoding or "utf-8", errors="replace")
    return _message_from_body(raw, response.status_code)


def _raise_for_status_with_body(response: httpx.Response, body: Optional[str]) -> None:
    """Map an HTTP error response to the appropriate ModusError subclass."""
    message = _message_from_body(body or "", response.status_code)
    status = response.status_code
    request_id = response.headers.get("x-request-id") or response.headers.get("X-Request-ID")
    headers = dict(response.headers)

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
        errors = None
        if body:
            try:
                errors = json.loads(body)
            except json.JSONDecodeError:
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


def _decode_body(body_bytes: bytes, response: httpx.Response) -> Optional[str]:
    return (
        body_bytes.decode(response.encoding or "utf-8", errors="replace")
        if body_bytes
        else None
    )


def _raise_for_status(response: httpx.Response) -> None:
    """Map an HTTP error response to the appropriate ModusError subclass."""
    if response.is_success:
        return
    body = _decode_body(_read_response_bytes(response), response)
    _raise_for_status_with_body(response, body)


async def _raise_for_status_async(response: httpx.Response) -> None:
    """Map an HTTP error response to ModusError (async streaming path)."""
    if response.is_success:
        return
    body = _decode_body(await _read_response_bytes_async(response), response)
    _raise_for_status_with_body(response, body)


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
                await _raise_for_status_async(response)
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
