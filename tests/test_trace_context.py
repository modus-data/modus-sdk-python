"""Every request carries a W3C ``traceparent``, so one id names a call on both sides: the
customer quotes ``error.trace_id``, and Modus finds the server work that call caused."""

from __future__ import annotations

import re
from typing import List
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx
from modus import APIConnectionError, ModusError, NotFoundError
from modus._config import ModusConfig
from modus._http import HttpClient
from modus.management import AsyncModusManagement, ModusManagement
from tests.fixtures.api_shapes import SAMPLE_SKILL

BASE = "https://api.modus.com"
KEY = "modus_test_key_abc123"
URL = f"{BASE}/api/v1/scopes/42"
TRACEPARENT = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-00$")


def trace_id_of(request: httpx.Request) -> str:
    match = TRACEPARENT.match(request.headers.get("traceparent", ""))
    assert match, request.headers.get("traceparent")
    assert match.group(1) != "0" * 32 and match.group(2) != "0" * 16
    return match.group(1)


def sent(route: respx.Route) -> List[httpx.Request]:
    return [call.request for call in route.calls]


def unavailable() -> httpx.Response:
    return httpx.Response(503, json={"message": "Service Unavailable"})


@respx.mock
def test_traceparent_is_well_formed_and_new_for_every_call() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(200, json=SAMPLE_SKILL))
    client = ModusManagement(api_key=KEY, base_url=BASE)
    client.scopes.get(42)
    client.scopes.get(42)
    first, second = (trace_id_of(r) for r in sent(route))
    assert first != second


@respx.mock
def test_retries_of_one_call_share_its_trace_and_are_numbered() -> None:
    route = respx.get(URL).mock(
        side_effect=[unavailable(), unavailable(), httpx.Response(200, json=SAMPLE_SKILL)]
    )
    with patch("modus._retry.time.sleep"):
        ModusManagement(api_key=KEY, base_url=BASE, max_retries=2).scopes.get(42)
    requests = sent(route)
    assert len({trace_id_of(r) for r in requests}) == 1
    assert len({r.headers["traceparent"] for r in requests}) == 3
    assert [r.headers.get("x-modus-retry-attempt") for r in requests] == [None, "1", "2"]


@pytest.mark.asyncio
@respx.mock
async def test_async_retries_share_one_trace() -> None:
    route = respx.get(URL).mock(
        side_effect=[
            unavailable(),
            httpx.Response(200, json=SAMPLE_SKILL),
            httpx.Response(200, json=SAMPLE_SKILL),
        ]
    )
    with patch("modus._retry.asyncio.sleep", AsyncMock()):
        async with AsyncModusManagement(api_key=KEY, base_url=BASE, max_retries=1) as client:
            await client.scopes.get(42)
            await client.scopes.get(42)
    requests = sent(route)
    assert [r.headers.get("x-modus-retry-attempt") for r in requests] == [None, "1", None]
    ids = [trace_id_of(r) for r in requests]
    assert ids[0] == ids[1] != ids[2]


@respx.mock
def test_a_callers_own_traceparent_is_kept() -> None:
    own = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    route = respx.get(URL).mock(return_value=httpx.Response(404, json={"message": "no"}))
    client = ModusManagement(
        api_key=KEY, base_url=BASE, max_retries=0, default_headers={"traceparent": own}
    )
    with pytest.raises(NotFoundError) as exc:
        client.scopes.get(42)
    assert sent(route)[0].headers.get_list("traceparent") == [own]
    assert exc.value.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"


@respx.mock
def test_error_trace_id_names_the_failed_call() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(404, json={"message": "no"}))
    with pytest.raises(NotFoundError) as exc:
        ModusManagement(api_key=KEY, base_url=BASE, max_retries=0).scopes.get(42)
    assert exc.value.trace_id == trace_id_of(sent(route)[0])


@respx.mock
def test_connection_error_carries_the_trace_id() -> None:
    route = respx.get(URL).mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(APIConnectionError) as exc:
        ModusManagement(api_key=KEY, base_url=BASE, max_retries=0).scopes.get(42)
    assert exc.value.trace_id == trace_id_of(sent(route)[0])


@respx.mock
def test_a_stream_carries_a_traceparent_and_its_error_the_trace_id() -> None:
    route = respx.post(f"{BASE}/agent/v1/modus/runs").mock(
        return_value=httpx.Response(500, json={"message": "boom"})
    )
    http = HttpClient(ModusConfig(api_key=KEY, base_url=BASE))
    with pytest.raises(ModusError) as exc:
        list(http.stream_post("/agent/v1/modus/runs", json={}))
    assert exc.value.trace_id == trace_id_of(sent(route)[0])
