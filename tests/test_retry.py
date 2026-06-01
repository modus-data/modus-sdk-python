"""Tests for retry logic."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from modus._exceptions import InternalServerError, NotFoundError, RateLimitError
from modus._retry import async_with_retry, with_retry


def test_success_no_retry():
    fn = MagicMock(return_value="ok")
    assert with_retry(fn, max_retries=2) == "ok"
    assert fn.call_count == 1


def test_non_retryable_raises_immediately(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    fn = MagicMock(side_effect=NotFoundError("not found"))
    with pytest.raises(NotFoundError):
        with_retry(fn, max_retries=3)
    assert fn.call_count == 1  # no retries for 404


def test_retries_on_server_error(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    fn = MagicMock(side_effect=[InternalServerError("fail", status_code=500), "ok"])
    assert with_retry(fn, max_retries=2) == "ok"
    assert fn.call_count == 2


def test_retries_on_rate_limit(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    fn = MagicMock(side_effect=[RateLimitError("429"), RateLimitError("429"), "ok"])
    assert with_retry(fn, max_retries=2) == "ok"
    assert fn.call_count == 3


def test_raises_after_max_retries(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    fn = MagicMock(side_effect=InternalServerError("always fails", status_code=500))
    with pytest.raises(InternalServerError):
        with_retry(fn, max_retries=2)
    assert fn.call_count == 3  # initial + 2 retries


def test_zero_retries_single_attempt(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    fn = MagicMock(side_effect=InternalServerError("fail", status_code=500))
    with pytest.raises(InternalServerError):
        with_retry(fn, max_retries=0)
    assert fn.call_count == 1


def test_first_retry_is_immediate(monkeypatch):
    slept = []
    monkeypatch.setattr("time.sleep", lambda s: slept.append(s))
    fn = MagicMock(side_effect=[InternalServerError("fail", status_code=500), "ok"])
    assert with_retry(fn, max_retries=2) == "ok"
    assert slept == [0.0]


def test_respects_retry_after_header(monkeypatch):
    slept = []
    monkeypatch.setattr("time.sleep", lambda s: slept.append(s))
    fn = MagicMock(side_effect=[RateLimitError("429", retry_after=42), "ok"])
    with_retry(fn, max_retries=2)
    assert slept[0] == 42.0


# ---------------------------------------------------------------------------
# async_with_retry tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_success_no_retry():
    fn = AsyncMock(return_value="ok")
    assert await async_with_retry(fn, max_retries=2) == "ok"
    assert fn.call_count == 1


@pytest.mark.asyncio
async def test_async_non_retryable_raises_immediately(monkeypatch):
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    fn = AsyncMock(side_effect=NotFoundError("not found"))
    with pytest.raises(NotFoundError):
        await async_with_retry(fn, max_retries=3)
    assert fn.call_count == 1  # no retries for 404


@pytest.mark.asyncio
async def test_async_retries_on_server_error(monkeypatch):
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    fn = AsyncMock(side_effect=[InternalServerError("fail", status_code=500), "ok"])
    assert await async_with_retry(fn, max_retries=2) == "ok"
    assert fn.call_count == 2


@pytest.mark.asyncio
async def test_async_raises_after_max_retries(monkeypatch):
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    fn = AsyncMock(side_effect=InternalServerError("always fails", status_code=500))
    with pytest.raises(InternalServerError):
        await async_with_retry(fn, max_retries=2)
    assert fn.call_count == 3  # initial + 2 retries


@pytest.mark.asyncio
async def test_async_first_retry_is_immediate(monkeypatch):
    slept = []

    async def fake_sleep(s):
        slept.append(s)

    monkeypatch.setattr("asyncio.sleep", fake_sleep)
    fn = AsyncMock(side_effect=[InternalServerError("fail", status_code=500), "ok"])
    assert await async_with_retry(fn, max_retries=2) == "ok"
    assert slept == [0.0]


@pytest.mark.asyncio
async def test_async_respects_retry_after_header(monkeypatch):
    slept = []

    async def fake_sleep(s):
        slept.append(s)

    monkeypatch.setattr("asyncio.sleep", fake_sleep)
    fn = AsyncMock(side_effect=[RateLimitError("429", retry_after=15), "ok"])
    await async_with_retry(fn, max_retries=2)
    assert slept[0] == 15.0
