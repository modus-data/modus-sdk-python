"""
Modus SDK exception hierarchy.

All exceptions raised by the SDK are subclasses of ModusError.
HTTP errors are mapped from status codes; run errors are raised from SSE events.

HTTP mapping:
    400 -> BadRequestError
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

from typing import Any, Dict, Mapping, Optional


class ModusError(Exception):
    """
    Base class for all Modus SDK errors.

    Attributes:
        request_id: The error envelope's ``requestId`` (or the ``x-request-id`` header);
            quote it to support.
        trace_id: The W3C trace id of the request that failed (from the ``traceparent``
            the SDK sent). Quote it with ``request_id``: it also names a request that never
            reached Modus, and every retry of it.
        code: Machine-readable error code from the envelope, e.g. ``NOT_FOUND``.
        info: Structured detail from the envelope, e.g. ``{"missing": ["scopes:write"]}``
            on a 403.
        retryable: Whether the SDK's retry rule allows re-sending this call. True for a
            429 whose Retry-After is absent or at most 60 s, and for a connection that
            never opened. For 408, 500, 502, 503, 504, a dropped connection or a timeout:
            true on GET, PUT, PATCH and DELETE and on POSTs that only read or set a
            state, false on any other POST, which may already have run. The SDK already
            retried a retryable error up to ``max_retries`` times.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        request_id: Optional[str] = None,
        response_headers: Optional[Mapping[str, str]] = None,
        body: Optional[str] = None,
        code: Optional[str] = None,
        info: Optional[Dict[str, Any]] = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.request_id = request_id
        self.trace_id: Optional[str] = None
        self.response_headers = dict(response_headers) if response_headers else None
        self.body = body
        self.code = code
        self.info = info
        self.retryable = retryable

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code!r}, "
            f"code={self.code!r}, "
            f"request_id={self.request_id!r})"
        )


class APIConnectionError(ModusError):
    """
    Network-level failure (connection refused, reset, timeout, etc.).

    ``retryable`` says whether the SDK re-sent it: always when the connection never
    opened, otherwise only for GET/PUT/PATCH/DELETE and POSTs that only read or set a state.
    """
    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message, retryable=retryable)


class BadRequestError(ModusError):
    """
    The request was malformed (HTTP 400): a parameter or body field failed schema
    validation, an unknown property was sent, or an id was not a number. ``message``
    names the field.
    """
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, status_code=400, **kwargs)


class AuthenticationError(ModusError):
    """
    The API key is missing, invalid, or expired (HTTP 401).

    Check that MODUS_API_KEY is set correctly, or pass api_key= explicitly.
    Create a token at app.getmodus.com → Settings → API Tokens.
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
    The request conflicts with existing state (HTTP 409).

    Inspect the API message for the operation-specific outcome. For ingested-data
    uploads, this means the complete payload is already stored and is a safe retry
    outcome.
    """
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, status_code=409, **kwargs)


class UnprocessableError(ModusError):
    """
    The request was well-formed but failed a business rule (HTTP 422, ``code: VALIDATION``),
    for example a toolset rule or a disallowed file type. Schema failures raise
    :class:`BadRequestError` (400) instead.

    ``info`` carries the rule detail when the server sends one (e.g. ``info["violations"]``);
    ``errors`` is the whole parsed error envelope.
    """
    def __init__(self, message: str, *, errors: Optional[Any] = None, **kwargs: Any) -> None:
        super().__init__(message, status_code=422, **kwargs)
        self.errors = errors


class RateLimitError(ModusError):
    """
    Rate limit exceeded (HTTP 429).

    ``retry_after`` is the server's requested wait in whole seconds, when it sent one
    (``retry-after-ms``, or ``Retry-After`` as seconds or an HTTP date). The SDK waits it
    out and retries when it is 60 s or less; a longer wait is raised at once.
    """
    def __init__(self, message: str, *, retry_after: Optional[int] = None, **kwargs: Any) -> None:
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after


class InternalServerError(ModusError):
    """
    The server or a gateway failed (HTTP 5xx).

    The SDK retries 500/502/503/504 except on a POST that may already have run (POSTs
    that only read or set a state are retried); ``retryable`` says which applied.
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


class ValidationError(ModusError, ValueError):
    """
    An argument failed client-side validation before any request was sent (for example a
    blank or ``".."`` id, or an unsupported chat model).

    It is also a ``ValueError``, so ``except ValueError`` keeps catching it.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
