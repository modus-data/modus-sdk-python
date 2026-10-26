"""The retry rule, Retry-After and response parsing, through the real transport."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx
from modus import APIConnectionError, AsyncModus, Modus, ModusError, RateLimitError
from modus._retry import is_retry_safe
from modus.management import ModusManagement
from modus.management.types.memories import MemorySearchRequest
from tests.fixtures.api_shapes import SAMPLE_SKILL

BASE = "https://api.modus.com"
KEY = "modus_test_key_abc123"


def mgmt(retries: int = 2) -> ModusManagement:
    return ModusManagement(api_key=KEY, base_url=BASE, max_retries=retries)


# A POST is not re-sent once it may have reached the server -----------------


@pytest.mark.parametrize(
    "first",
    [
        httpx.Response(504, json={"message": "Endpoint request timed out"}),
        httpx.Response(502, json={"message": "Bad Gateway"}),
        httpx.ReadTimeout("timed out"),
        httpx.ReadError("Connection reset by peer"),
        httpx.RemoteProtocolError("Server disconnected without sending a response."),
    ],
    ids=["504", "502", "ReadTimeout", "ReadError", "RemoteProtocolError"],
)
@respx.mock
def test_post_create_is_not_resent(first) -> None:
    route = respx.post(f"{BASE}/api/v1/scopes").mock(
        side_effect=[first, httpx.Response(201, json=SAMPLE_SKILL)]
    )
    with patch("modus._retry.time.sleep"), pytest.raises(ModusError) as exc:
        mgmt().scopes.create(name="retry")
    assert exc.value.retryable is False
    assert route.call_count == 1


@pytest.mark.parametrize(
    "first",
    [
        httpx.ConnectError("refused"),
        httpx.ConnectTimeout("connect timed out"),
        httpx.PoolTimeout("pool timed out"),
        httpx.Response(429, json={"message": "slow down"}, headers={"retry-after": "0"}),
    ],
    ids=["ConnectError", "ConnectTimeout", "PoolTimeout", "429"],
)
@respx.mock
def test_post_create_is_resent_when_nothing_ran(first) -> None:
    route = respx.post(f"{BASE}/api/v1/scopes").mock(
        side_effect=[first, httpx.Response(201, json=SAMPLE_SKILL)]
    )
    with patch("modus._retry.time.sleep"):
        mgmt().scopes.create(name="retry")
    assert route.call_count == 2


@respx.mock
def test_post_flagged_idempotent_is_resent_on_502() -> None:
    route = respx.post(f"{BASE}/api/v1/scopes/7/memories/search").mock(
        side_effect=[
            httpx.Response(502, json={"message": "Bad Gateway"}),
            httpx.Response(200, json={"memories": []}),
        ]
    )
    with patch("modus._retry.time.sleep"):
        mgmt().scopes.memories(7).search(MemorySearchRequest(query="x"))
    assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_async_post_create_is_not_resent() -> None:
    from modus.management import AsyncModusManagement

    route = respx.post(f"{BASE}/api/v1/scopes").mock(
        side_effect=[httpx.ReadError("reset"), httpx.Response(201, json=SAMPLE_SKILL)]
    )
    with patch("modus._retry.asyncio.sleep", AsyncMock()), pytest.raises(APIConnectionError):
        async with AsyncModusManagement(api_key=KEY, base_url=BASE, max_retries=2) as client:
            await client.scopes.create(name="retry")
    assert route.call_count == 1


# GET is retried on transient failures ---------------------------------------


@pytest.mark.parametrize(
    "first",
    [
        httpx.Response(502, json={"message": "Bad Gateway"}),
        httpx.Response(408, json={"message": "Request Timeout"}),
        httpx.ReadError("Connection reset by peer"),
        httpx.WriteError("Broken pipe"),
        httpx.CloseError("close"),
    ],
    ids=["502", "408", "ReadError", "WriteError", "CloseError"],
)
@respx.mock
def test_get_is_retried(first) -> None:
    route = respx.get(f"{BASE}/api/v1/scopes/42").mock(
        side_effect=[first, httpx.Response(200, json=SAMPLE_SKILL)]
    )
    with patch("modus._retry.time.sleep"):
        mgmt().scopes.get(42)
    assert route.call_count == 2


@respx.mock
def test_get_501_is_not_retried() -> None:
    route = respx.get(f"{BASE}/api/v1/scopes/42").mock(
        return_value=httpx.Response(501, json={"message": "Not Implemented"})
    )
    with patch("modus._retry.time.sleep"), pytest.raises(ModusError):
        mgmt().scopes.get(42)
    assert route.call_count == 1


@respx.mock
def test_transport_errors_surface_as_api_connection_error() -> None:
    respx.get(f"{BASE}/api/v1/scopes/42").mock(side_effect=httpx.ReadError("reset"))
    with patch("modus._retry.time.sleep"), pytest.raises(APIConnectionError) as exc:
        mgmt().scopes.get(42)
    assert exc.value.retryable is True


# Retry-After ----------------------------------------------------------------


@respx.mock
def test_retry_after_over_60s_raises_without_sleeping() -> None:
    route = respx.get(f"{BASE}/api/v1/scopes/42").mock(
        return_value=httpx.Response(429, json={"message": "slow down"}, headers={"retry-after": "86400"})
    )
    slept: list[float] = []
    with patch("modus._retry.time.sleep", side_effect=slept.append), pytest.raises(RateLimitError) as exc:
        mgmt().scopes.get(42)
    assert exc.value.retry_after == 86400
    assert slept == []
    assert route.call_count == 1


@respx.mock
def test_retry_after_up_to_60s_is_slept() -> None:
    respx.get(f"{BASE}/api/v1/scopes/42").mock(
        side_effect=[
            httpx.Response(429, json={"message": "slow down"}, headers={"retry-after": "7"}),
            httpx.Response(200, json=SAMPLE_SKILL),
        ]
    )
    slept: list[float] = []
    with patch("modus._retry.time.sleep", side_effect=slept.append):
        mgmt().scopes.get(42)
    assert slept == [7]


@respx.mock
def test_retry_after_http_date() -> None:
    when = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=5), usegmt=True)
    respx.get(f"{BASE}/api/v1/scopes/42").mock(
        return_value=httpx.Response(429, json={"message": "x"}, headers={"retry-after": when})
    )
    with pytest.raises(RateLimitError) as exc:
        mgmt(0).scopes.get(42)
    assert exc.value.retry_after in (4, 5)


@respx.mock
def test_retry_after_ms_wins() -> None:
    respx.get(f"{BASE}/api/v1/scopes/42").mock(
        side_effect=[
            httpx.Response(
                429,
                json={"message": "slow down"},
                headers={"retry-after-ms": "1500", "retry-after": "30"},
            ),
            httpx.Response(200, json=SAMPLE_SKILL),
        ]
    )
    slept: list[float] = []
    with patch("modus._retry.time.sleep", side_effect=slept.append):
        mgmt().scopes.get(42)
    assert slept == [2]


# 2xx bodies -----------------------------------------------------------------


@respx.mock
def test_non_json_200_is_one_non_retryable_modus_error() -> None:
    route = respx.get(f"{BASE}/api/v1/scopes/42").mock(
        return_value=httpx.Response(
            200, text="<html>Service Unavailable</html>", headers={"content-type": "text/html"}
        )
    )
    with patch("modus._retry.time.sleep"), pytest.raises(ModusError) as exc:
        mgmt().scopes.get(42)
    assert not isinstance(exc.value, APIConnectionError)
    assert exc.value.status_code == 200
    assert exc.value.message == (
        "Invalid JSON in HTTP 200 response (content-type \"text/html\"): "
        "<html>Service Unavailable</html>"
    )
    assert route.call_count == 1


@respx.mock
def test_empty_200_on_get_is_none() -> None:
    respx.get(f"{BASE}/api/v1/scopes").mock(return_value=httpx.Response(200, content=b""))
    client = Modus(api_key=KEY, base_url=BASE)
    assert client._http.get("/api/v1/scopes") is None


@pytest.mark.asyncio
@respx.mock
async def test_async_empty_200_on_get_is_none() -> None:
    respx.get(f"{BASE}/api/v1/scopes").mock(return_value=httpx.Response(200, content=b""))
    async with AsyncModus(api_key=KEY, base_url=BASE) as client:
        assert await client._http.get("/api/v1/scopes") is None


# The rule itself --------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "status", "expected"),
    [
        ("GET", 502, True),
        ("DELETE", 503, True),
        ("PATCH", 500, True),
        ("PUT", 504, True),
        ("GET", 408, True),
        ("GET", 501, False),
        ("GET", 404, False),
        ("POST", 502, False),
        ("POST", 500, False),
        ("POST", 408, False),
        ("POST", 429, True),
    ],
)
def test_is_retry_safe_by_status(method: str, status: int, expected: bool) -> None:
    assert is_retry_safe(method, False, status=status) is expected


def test_is_retry_safe_rules() -> None:
    assert is_retry_safe("POST", True, status=502) is True
    assert is_retry_safe("POST", False, exc=httpx.ConnectError("refused")) is True
    assert is_retry_safe("POST", False, exc=httpx.ReadError("reset")) is False
    assert is_retry_safe("POST", True, exc=httpx.ReadError("reset")) is True
    assert is_retry_safe("GET", False, exc=httpx.ReadError("reset")) is True
    assert is_retry_safe("GET", False, status=429, retry_after=60) is True
    assert is_retry_safe("GET", False, status=429, retry_after=61) is False
