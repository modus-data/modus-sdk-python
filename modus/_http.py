"""
HTTP transport layer.

HttpClient and AsyncHttpClient are thin wrappers around httpx that handle:
  - Auth header injection (via ModusConfig)
  - Response parsing (JSON, or None for 204 / an empty body)
  - HTTP status code → typed exception mapping, marking each error ``retryable``
  - Raw SSE line streaming (for skill execution)

Retry logic lives in _retry.py and is applied at the resource layer,
not here. This keeps each layer's responsibility clear.
"""

from __future__ import annotations

import json
import math
import platform
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from importlib.metadata import PackageNotFoundError, version
from typing import Any, AsyncIterator, Dict, Iterator, NamedTuple, Optional

import httpx

from ._auth import auth_headers
from ._config import ModusConfig
from ._exceptions import (
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    ModusError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableError,
)
from ._retry import is_retry_safe

try:
    _SDK_VERSION = version("modus")
except PackageNotFoundError:
    _SDK_VERSION = "0.0.0+dev"

_USER_AGENT = (
    f"modus-python/{_SDK_VERSION} "
    f"(python/{platform.python_version()}; {platform.system().lower()})"
)


_NETWORK_ERRORS = (httpx.TransportError,)


def _request_url(path: str, base_url: Optional[str]) -> str:
    if base_url is None:
        return path
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _wrap_network_error(
    exc: Exception, base_url: str, method: str = "GET", idempotent: bool = False
) -> APIConnectionError:
    """Convert any network-level httpx error into a typed APIConnectionError."""
    return APIConnectionError(
        f"Network error communicating with Modus API at {base_url!r}: {exc}. "
        "Check connectivity and that base_url is correct.",
        retryable=is_retry_safe(method, idempotent, exc=exc),
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


class _ErrorFields(NamedTuple):
    message: str
    code: Optional[str] = None
    request_id: Optional[str] = None
    info: Optional[Dict[str, Any]] = None
    parsed: Any = None


def _non_empty_str(value: Any) -> Optional[str]:
    return value if isinstance(value, str) and value else None


def _parse_error_body(raw: str, status_code: int) -> _ErrorFields:
    """
    Read an error body once: Modus's envelope ``{"error": {code, message, requestId, info}}``,
    an API Gateway body ``{"message": "..."}``, or anything else as raw text.
    """
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return _ErrorFields(raw or f"HTTP {status_code}")
    if not isinstance(parsed, dict):
        return _ErrorFields(raw, parsed=parsed)
    envelope = parsed.get("error")
    if isinstance(envelope, dict):
        info = envelope.get("info")
        return _ErrorFields(
            _non_empty_str(envelope.get("message")) or raw,
            code=_non_empty_str(envelope.get("code")),
            request_id=_non_empty_str(envelope.get("requestId")),
            info=info if isinstance(info, dict) else None,
            parsed=parsed,
        )
    message = parsed["message"] if parsed.get("message") is not None else parsed.get("error")
    if isinstance(message, list):
        return _ErrorFields("; ".join(str(m) for m in message), parsed=parsed)
    return _ErrorFields(_non_empty_str(message) or raw, parsed=parsed)


def _parse_retry_after(headers: httpx.Headers) -> Optional[int]:
    """
    Seconds to wait, from ``retry-after-ms`` or ``Retry-After`` (delta-seconds or an
    HTTP date), rounded up to whole seconds.
    """
    ms = (headers.get("retry-after-ms") or "").strip()
    if re.fullmatch(r"[0-9]+(\.[0-9]+)?", ms):
        return math.ceil(float(ms) / 1000)
    value = (headers.get("retry-after") or "").strip()
    if not value:
        return None
    if re.fullmatch(r"[0-9]+", value):
        return int(value)
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return max(0, math.ceil((when - datetime.now(timezone.utc)).total_seconds()))


def _raise_for_status_with_body(
    response: httpx.Response,
    body: Optional[str],
    method: str = "GET",
    idempotent: bool = False,
) -> None:
    """Map an HTTP error response to the appropriate ModusError subclass."""
    status = response.status_code
    fields = _parse_error_body(body or "", status)
    retry_after = _parse_retry_after(response.headers) if status == 429 else None
    kwargs: Dict[str, Any] = dict(
        request_id=fields.request_id or response.headers.get("x-request-id"),
        response_headers=dict(response.headers),
        body=body,
        code=fields.code,
        info=fields.info,
        retryable=is_retry_safe(method, idempotent, status=status, retry_after=retry_after),
    )
    message = fields.message

    if status == 400:
        raise BadRequestError(message, **kwargs)
    if status == 401:
        raise AuthenticationError(message, **kwargs)
    if status == 403:
        raise PermissionDeniedError(message, **kwargs)
    if status == 404:
        raise NotFoundError(message, **kwargs)
    if status == 409:
        raise ConflictError(message, **kwargs)
    if status == 422:
        raise UnprocessableError(message, errors=fields.parsed, **kwargs)
    if status == 429:
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


def _raise_for_status(
    response: httpx.Response, method: str = "GET", idempotent: bool = False
) -> None:
    """Map an HTTP error response to the appropriate ModusError subclass."""
    if response.is_success:
        return
    body = _decode_body(_read_response_bytes(response), response)
    _raise_for_status_with_body(response, body, method, idempotent)


async def _raise_for_status_async(response: httpx.Response, method: str) -> None:
    """Map an HTTP error response to ModusError (async streaming path)."""
    if response.is_success:
        return
    body = _decode_body(await _read_response_bytes_async(response), response)
    _raise_for_status_with_body(response, body, method)


def _json_or_none(response: httpx.Response) -> Any:
    """Parse a 2xx body: None for 204 or an empty body; one that is not JSON is a non-retryable ModusError."""
    if response.status_code == 204 or not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        content_type = response.headers.get("content-type", "")
        raise ModusError(
            f"Invalid JSON in HTTP {response.status_code} response "
            f"(content-type {json.dumps(content_type)}): {response.text[:200]}",
            status_code=response.status_code,
            request_id=response.headers.get("x-request-id"),
            response_headers=dict(response.headers),
            body=response.text,
        ) from None


def _ensure_sse_content_type(response: httpx.Response, body_preview: str = "") -> None:
    """Reject non-SSE responses so empty streams never look like success."""
    ct = (response.headers.get("content-type") or "").lower()
    if "text/event-stream" in ct:
        return
    preview = body_preview[:200]
    raise ModusError(
        f"Unexpected stream response: expected Content-Type text/event-stream, "
        f"got {response.headers.get('content-type')!r}. "
        f"Body preview: {preview}",
        status_code=response.status_code,
        body=preview or None,
    )


def _sse_body_preview_from_lines(lines: Iterator[str], limit: int = 200) -> str:
    """Accumulate at most ``limit`` characters from an iterator of lines."""
    preview = ""
    for line in lines:
        remaining = limit - len(preview)
        if remaining <= 0:
            break
        preview += line[:remaining]
        if len(preview) >= limit:
            break
    return preview


def _client_headers(config: ModusConfig) -> httpx.Headers:
    headers = httpx.Headers(
        {"Accept": "application/json", "User-Agent": _USER_AGENT, "X-Modus-Client": "sdk"}
    )
    headers.update(config.default_headers)
    headers.update(auth_headers(config.api_key))
    return headers


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
            headers=_client_headers(config),
            timeout=config.timeout,
        )

    @property
    def config(self) -> ModusConfig:
        return self._config

    def _send(
        self,
        method: str,
        path: str,
        *,
        base_url: Optional[str],
        idempotent: bool = False,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        try:
            response = self._client.request(
                method, _request_url(path, base_url), params=params, json=json
            )
        except _NETWORK_ERRORS as exc:
            raise _wrap_network_error(
                exc, base_url or self._config.base_url, method, idempotent
            ) from exc
        _raise_for_status(response, method, idempotent)
        return _json_or_none(response)

    def get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
    ) -> Any:
        return self._send("GET", path, params=params, base_url=base_url)

    def post(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
        idempotent: bool = False,
    ) -> Any:
        """``idempotent``: the POST only reads or sets a state, so it is safe to re-send."""
        return self._send("POST", path, json=json, base_url=base_url, idempotent=idempotent)

    def patch(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
    ) -> Any:
        return self._send("PATCH", path, json=json, params=params, base_url=base_url)

    def put(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
    ) -> Any:
        return self._send("PUT", path, json=json, params=params, base_url=base_url)

    def delete(self, path: str, *, base_url: Optional[str] = None) -> Optional[Any]:
        return self._send("DELETE", path, base_url=base_url)

    def stream_post(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Make a streaming POST and yield raw SSE lines.

        The caller is responsible for parsing SSE syntax.
        """
        yield from self.stream("POST", path, json=json, base_url=base_url)

    def stream(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
    ) -> Iterator[str]:
        """Make a streaming request and yield raw SSE lines."""
        effective_base_url = base_url or self._config.base_url
        try:
            # Override client default Accept: application/json — agent-service
            # negotiates SSE vs JSON polling on Accept.
            with self._client.stream(
                method,
                _request_url(path, base_url),
                json=json,
                headers={"Accept": "text/event-stream"},
            ) as response:
                _raise_for_status(response, method)
                ct = (response.headers.get("content-type") or "").lower()
                if "text/event-stream" not in ct:
                    preview = _sse_body_preview_from_lines(response.iter_lines())
                    _ensure_sse_content_type(response, preview)
                for line in response.iter_lines():
                    if line.strip():
                        yield line
        except _NETWORK_ERRORS as exc:
            raise _wrap_network_error(exc, effective_base_url, method) from exc

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
            headers=_client_headers(config),
            timeout=config.timeout,
        )

    @property
    def config(self) -> ModusConfig:
        return self._config

    async def _send(
        self,
        method: str,
        path: str,
        *,
        base_url: Optional[str],
        idempotent: bool = False,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        try:
            response = await self._client.request(
                method, _request_url(path, base_url), params=params, json=json
            )
        except _NETWORK_ERRORS as exc:
            raise _wrap_network_error(
                exc, base_url or self._config.base_url, method, idempotent
            ) from exc
        _raise_for_status(response, method, idempotent)
        return _json_or_none(response)

    async def get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
    ) -> Any:
        return await self._send("GET", path, params=params, base_url=base_url)

    async def post(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
        idempotent: bool = False,
    ) -> Any:
        """``idempotent``: the POST only reads or sets a state, so it is safe to re-send."""
        return await self._send(
            "POST", path, json=json, base_url=base_url, idempotent=idempotent
        )

    async def patch(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
    ) -> Any:
        return await self._send("PATCH", path, json=json, params=params, base_url=base_url)

    async def put(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
    ) -> Any:
        return await self._send("PUT", path, json=json, params=params, base_url=base_url)

    async def delete(self, path: str, *, base_url: Optional[str] = None) -> Optional[Any]:
        return await self._send("DELETE", path, base_url=base_url)

    async def stream_post(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Streaming POST — yields raw SSE lines."""
        async for line in self.stream("POST", path, json=json, base_url=base_url):
            yield line

    async def stream(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Streaming request — yields raw SSE lines."""
        effective_base_url = base_url or self._config.base_url
        try:
            async with self._client.stream(
                method,
                _request_url(path, base_url),
                json=json,
                headers={"Accept": "text/event-stream"},
            ) as response:
                await _raise_for_status_async(response, method)
                ct = (response.headers.get("content-type") or "").lower()
                if "text/event-stream" not in ct:
                    chunks: list[str] = []
                    size = 0
                    async for line in response.aiter_lines():
                        remaining = 200 - size
                        if remaining <= 0:
                            break
                        piece = line[:remaining]
                        chunks.append(piece)
                        size += len(piece)
                        if size >= 200:
                            break
                    _ensure_sse_content_type(response, "".join(chunks))
                async for line in response.aiter_lines():
                    if line.strip():
                        yield line
        except _NETWORK_ERRORS as exc:
            raise _wrap_network_error(exc, effective_base_url, method) from exc

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncHttpClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
