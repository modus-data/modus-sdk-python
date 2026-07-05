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

from ._exceptions import APIConnectionError, InternalServerError, NotFoundError, RateLimitError

T = TypeVar("T")

_RETRYABLE_ERRORS = (RateLimitError, InternalServerError, APIConnectionError)
_DEPLOY_NOT_FOUND_BACKOFF_SECONDS = 0.5
_MAX_DEPLOY_NOT_FOUND_RETRIES = 1


def _backoff_seconds(attempt: int, exc: Exception) -> float:
    """Calculate how long to sleep before the next retry attempt."""
    if isinstance(exc, RateLimitError) and exc.retry_after is not None:
        return max(0.0, float(exc.retry_after))
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
    Call func, retrying on RateLimitError, InternalServerError, and APIConnectionError.

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
    while True:
        try:
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
        except _RETRYABLE_ERRORS as exc:
            if attempt >= max_retries:
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
    while True:
        try:
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
        except _RETRYABLE_ERRORS as exc:
            if attempt >= max_retries:
                raise
            await asyncio.sleep(_backoff_seconds(attempt, exc))
            attempt += 1
