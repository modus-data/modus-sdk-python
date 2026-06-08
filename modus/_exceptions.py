"""
Modus SDK exception hierarchy.

All exceptions raised by the SDK are subclasses of ModusError.
HTTP errors are mapped from status codes; run errors are raised from SSE events.

HTTP mapping:
    401 -> AuthenticationError
    403 -> PermissionDeniedError
    404 -> NotFoundError
    409 -> ConflictError
    422 -> UnprocessableError
    429 -> RateLimitError
    5xx -> InternalServerError

SSE event mapping:
    { type: "error" }        -> ModusError (raised from run/stream)
    { type: "cancelled" }    -> RunCancelledError
    { type: "stream_timeout" } -> StreamTimeoutError
"""

from __future__ import annotations

from typing import Any, Mapping, Optional


class ModusError(Exception):
    """Base class for all Modus SDK errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        request_id: Optional[str] = None,
        response_headers: Optional[Mapping[str, str]] = None,
        body: Optional[str] = None,
        code: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.request_id = request_id
        self.response_headers = dict(response_headers) if response_headers else None
        self.body = body
        self.code = code

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code!r}, "
            f"request_id={self.request_id!r})"
        )


class APIConnectionError(ModusError):
    """
    Network-level failure (ConnectError, ReadTimeout, etc.) after all
    automatic retries are exhausted.
    """
    def __init__(self, message: str) -> None:
        super().__init__(message)


class AuthenticationError(ModusError):
    """
    The API key is missing, invalid, or expired (HTTP 401).

    Check that MODUS_API_KEY is set correctly, or pass api_key= explicitly.
    Create a token at app.modus.com → Settings → API Tokens.
    """
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, status_code=401, **kwargs)


class PermissionDeniedError(ModusError):
    """Raised when the API key does not have permission for the requested operation (HTTP 403)."""
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, status_code=403, **kwargs)


class NotFoundError(ModusError):
    """The requested resource does not exist (HTTP 404)."""
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, status_code=404, **kwargs)


class ConflictError(ModusError):
    """
    Idempotency conflict — a run with this ID already exists with a different
    body (HTTP 409). Use a new idempotency key or omit it to auto-generate.
    """
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, status_code=409, **kwargs)


class UnprocessableError(ModusError):
    """
    Request validation failed (HTTP 422).
    The `errors` attribute contains the full validation error detail.
    """
    def __init__(self, message: str, *, errors: Optional[Any] = None, **kwargs: Any) -> None:
        super().__init__(message, status_code=422, **kwargs)
        self.errors = errors


class RateLimitError(ModusError):
    """
    Rate limit exceeded (HTTP 429).

    The `retry_after` attribute contains the number of seconds to wait
    before retrying, if the server provided a Retry-After header.
    The SDK retries automatically — this error only surfaces after all
    retry attempts are exhausted.
    """
    def __init__(self, message: str, *, retry_after: Optional[int] = None, **kwargs: Any) -> None:
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after


class InternalServerError(ModusError):
    """
    The server encountered an internal error (HTTP 5xx).
    The SDK retries automatically — this error only surfaces after all
    retry attempts are exhausted.
    """
    def __init__(self, message: str, *, status_code: int, **kwargs: Any) -> None:
        super().__init__(message, status_code=status_code, **kwargs)


# ---------------------------------------------------------------------------
# Run-specific errors (raised from SSE events, not HTTP status codes)
# ---------------------------------------------------------------------------


class RunCancelledError(ModusError):
    """Raised when a chat stream is cancelled before completing."""

    def __init__(self, message: str = "Run was cancelled.") -> None:
        super().__init__(message)


class StreamTimeoutError(ModusError):
    """Raised when a chat stream times out before completion."""

    def __init__(self, message: str = "Stream timed out.") -> None:
        super().__init__(message)

