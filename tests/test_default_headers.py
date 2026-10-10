"""X-Modus-Client identification and the default_headers merge rule."""

from __future__ import annotations

from typing import Mapping

import httpx
import pytest
import respx
from modus import AsyncModus, Modus
from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient
from modus.management import AsyncModusManagement, ModusManagement

BASE = "https://api.example.com"
KEY = "modus_test_key_headers"

CASES = [
    ({}, {"X-Modus-Client": "sdk"}),
    ({"x-modus-client": "cli", "X-Extra": "1"}, {"X-Modus-Client": "cli", "X-Extra": "1"}),
    ({"authorization": "Bearer other"}, {"Authorization": f"Bearer {KEY}"}),
]


def _mock_routes() -> tuple[respx.Route, respx.Route]:
    json_route = respx.get(f"{BASE}/api/v1/scopes").mock(return_value=httpx.Response(200, json={}))
    sse_route = respx.post(f"{BASE}/agent/v1/modus/runs").mock(
        return_value=httpx.Response(
            200, headers={"Content-Type": "text/event-stream"}, text="data: {}\n\n"
        )
    )
    return json_route, sse_route


def _assert_sent(route: respx.Route, expected: Mapping[str, str]) -> None:
    headers = route.calls[0].request.headers
    for name, value in expected.items():
        assert headers.get_list(name) == [value]


@pytest.mark.parametrize(("default_headers", "expected"), CASES)
@respx.mock
def test_sync_json_and_sse(default_headers: dict, expected: dict) -> None:
    json_route, sse_route = _mock_routes()
    http = HttpClient(ModusConfig(api_key=KEY, base_url=BASE, default_headers=default_headers))
    http.get("/api/v1/scopes")
    list(http.stream_post("/agent/v1/modus/runs", json={}))
    _assert_sent(json_route, expected)
    _assert_sent(sse_route, expected)


@pytest.mark.parametrize(("default_headers", "expected"), CASES)
@respx.mock
async def test_async_json_and_sse(default_headers: dict, expected: dict) -> None:
    json_route, sse_route = _mock_routes()
    http = AsyncHttpClient(
        ModusConfig(api_key=KEY, base_url=BASE, default_headers=default_headers)
    )
    await http.get("/api/v1/scopes")
    async for _ in http.stream_post("/agent/v1/modus/runs", json={}):
        pass
    _assert_sent(json_route, expected)
    _assert_sent(sse_route, expected)


@pytest.mark.parametrize("client_cls", [Modus, AsyncModus, ModusManagement, AsyncModusManagement])
def test_clients_pass_default_headers_to_config(client_cls: type) -> None:
    client = client_cls(api_key=KEY, default_headers={"X-Extra": "1"})
    assert client._config.default_headers == {"X-Extra": "1"}


@pytest.mark.parametrize("client_cls", [Modus, AsyncModus])
def test_agent_host_client_gets_default_headers(client_cls: type) -> None:
    client = client_cls(api_key=KEY, default_headers={"X-Extra": "1"})
    assert client._agent_http.config.default_headers == {"X-Extra": "1"}
