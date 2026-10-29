"""
Retry logic for transient errors.

The transport marks each ModusError ``retryable`` with :func:`is_retry_safe`; with_retry
re-sends only those. Client errors (4xx except 408/429) are never retried.

Backoff strategy:
  - attempt 0 -> no sleep (immediate retry)
  - attempt 1 -> ~1s + jitter
  - attempt 2 -> ~2s + jitter
  - A 429's Retry-After (60 s or less) is slept instead.
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Awaitable, Callable, Optional, TypeVar

import httpx

from ._exceptions import ModusError, NotFoundError, RateLimitError
from ._trace import call_send, new_trace_id

T = TypeVar("T")

#: The longest Retry-After the SDK sleeps; a longer one is raised as RateLimitError at once.
MAX_RETRY_AFTER_SECONDS = 60

_RETRY_STATUSES = frozenset({408, 429, 500, 502, 503, 504})
# Raised before any request byte was written.
_CONNECT_PHASE_ERRORS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout)
_DEPLOY_NOT_FOUND_BACKOFF_SECONDS = 0.5
_MAX_DEPLOY_NOT_FOUND_RETRIES = 1


def is_retry_safe(
    method: str,
    idempotent: bool,
    *,
    status: Optional[int] = None,
    retry_after: Optional[int] = None,
    exc: Optional[Exception] = None,
) -> bool:
    """
    The SDK's one retry rule: may this request be sent again without doing its work twice?

    - 429: yes (the rate limiter rejected it before any work), unless Retry-After exceeds 60 s.
    - A connect-phase failure (refused, DNS, connect or pool timeout): yes, nothing was sent.
    - 408, 500, 502, 503, 504, or a failure after sending (reset, read timeout): only for
      GET/PUT/PATCH/DELETE, and for a POST whose operation only reads or sets a state.
      Any other POST may already have run on the server.

    Pass ``status`` for an HTTP response, or ``exc`` for an httpx transport error.
    """
    if status is not None:
        if status == 429:
            return (retry_after or 0) <= MAX_RETRY_AFTER_SECONDS
        if status not in _RETRY_STATUSES:
            return False
    elif isinstance(exc, _CONNECT_PHASE_ERRORS):
        return True
    return method != "POST" or idempotent


def _backoff_seconds(attempt: int, exc: ModusError) -> float:
    """Calculate how long to sleep before the next retry attempt."""
    if isinstance(exc, RateLimitError) and exc.retry_after is not None:
        return float(exc.retry_after)
    if attempt == 0:
        return 0.0
    # Exponential backoff: 1s, 2s, ... with ±0.3s jitter
    return max(0.5, (2 ** (attempt - 1)) + (random.random() * 0.6 - 0.3))


def with_retry(
    func: Callable[[], T],
    max_retries: int,
    *,
    retry_not_found_on_deploy: bool = False,
) -> T:
    """
    Call func, re-sending while it raises a ModusError marked ``retryable``.

    Args:
        func:        Zero-argument callable to invoke.
        max_retries: Maximum number of additional attempts after the first.
                     0 means no retries (single attempt total).
        retry_not_found_on_deploy:
                     When True, retry HTTP 404 once with a short fixed delay.
                     This deploy-specific retry does not consume max_retries.

    Returns:
        The return value of func on success.

    Raises:
        The last exception if all attempts are exhausted.
        Any non-retryable exception immediately (no retry).
    """
    deploy_not_found_retries = 0
    attempt = 0
    # One trace for the call and its re-sends; the transport reads it per request.
    trace_id = new_trace_id()
    sends = 0
    while True:
        try:
            with call_send(trace_id, sends):
                sends += 1
                return func()
        except NotFoundError:
            if (
                retry_not_found_on_deploy
                and deploy_not_found_retries < _MAX_DEPLOY_NOT_FOUND_RETRIES
            ):
                deploy_not_found_retries += 1
                time.sleep(_DEPLOY_NOT_FOUND_BACKOFF_SECONDS)
                continue
            raise
        except ModusError as exc:
            if not exc.retryable or attempt >= max_retries:
                raise
            time.sleep(_backoff_seconds(attempt, exc))
            attempt += 1


async def async_with_retry(
    func: Callable[[], Awaitable[T]],
    max_retries: int,
    *,
    retry_not_found_on_deploy: bool = False,
) -> T:
    """
    Async version of with_retry. Uses asyncio.sleep so the event loop is
    not blocked during backoff waits.

    Args:
        func:        Zero-argument async callable (coroutine function) to invoke.
        max_retries: Maximum number of additional attempts after the first.
        retry_not_found_on_deploy:
                     When True, retry HTTP 404 once with a short fixed delay.
                     This deploy-specific retry does not consume max_retries.

    Returns:
        The return value of func on success.
    """
    deploy_not_found_retries = 0
    attempt = 0
    trace_id = new_trace_id()
    sends = 0
    while True:
        try:
            with call_send(trace_id, sends):
                sends += 1
                return await func()
        except NotFoundError:
            if (
                retry_not_found_on_deploy
                and deploy_not_found_retries < _MAX_DEPLOY_NOT_FOUND_RETRIES
            ):
                deploy_not_found_retries += 1
                await asyncio.sleep(_DEPLOY_NOT_FOUND_BACKOFF_SECONDS)
                continue
            raise
        except ModusError as exc:
            if not exc.retryable or attempt >= max_retries:
                raise
            await asyncio.sleep(_backoff_seconds(attempt, exc))
            attempt += 1
