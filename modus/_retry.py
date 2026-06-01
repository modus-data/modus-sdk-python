"""
Retry logic for transient errors.

RateLimitError, InternalServerError, and APIConnectionError are retried.
Client errors (4xx except 429) are not retried — they represent caller mistakes.

Backoff strategy:
  - attempt 0 -> no sleep (immediate retry)
  - attempt 1 -> ~1s + jitter
  - attempt 2 -> ~2s + jitter
  - If Retry-After header is present on 429, use that value instead.
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Awaitable, Callable, TypeVar

from ._exceptions import APIConnectionError, InternalServerError, RateLimitError

T = TypeVar("T")

_RETRYABLE_ERRORS = (RateLimitError, InternalServerError, APIConnectionError)


def _backoff_seconds(attempt: int, exc: Exception) -> float:
    """Calculate how long to sleep before the next retry attempt."""
    if isinstance(exc, RateLimitError) and exc.retry_after is not None:
        return max(0.0, float(exc.retry_after))
    if attempt == 0:
        return 0.0
    # Exponential backoff: 1s, 2s, ... with ±0.3s jitter
    return max(0.5, (2 ** (attempt - 1)) + (random.random() * 0.6 - 0.3))


def with_retry(func: Callable[[], T], max_retries: int) -> T:
    """
    Call func, retrying on RateLimitError, InternalServerError, and APIConnectionError.

    Args:
        func:        Zero-argument callable to invoke.
        max_retries: Maximum number of additional attempts after the first.
                     0 means no retries (single attempt total).

    Returns:
        The return value of func on success.

    Raises:
        The last exception if all attempts are exhausted.
        Any non-retryable exception immediately (no retry).
    """
    for attempt in range(max_retries + 1):
        try:
            return func()
        except _RETRYABLE_ERRORS as exc:
            if attempt == max_retries:
                raise
            time.sleep(_backoff_seconds(attempt, exc))

    raise RuntimeError("unreachable")  # satisfies type checker


async def async_with_retry(
    func: Callable[[], Awaitable[T]], max_retries: int
) -> T:
    """
    Async version of with_retry. Uses asyncio.sleep so the event loop is
    not blocked during backoff waits.

    Args:
        func:        Zero-argument async callable (coroutine function) to invoke.
        max_retries: Maximum number of additional attempts after the first.

    Returns:
        The return value of func on success.
    """
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except _RETRYABLE_ERRORS as exc:
            if attempt == max_retries:
                raise
            await asyncio.sleep(_backoff_seconds(attempt, exc))

    raise RuntimeError("unreachable")  # satisfies type checker
