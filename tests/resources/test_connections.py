"""Tests for client.connections.list() and find()."""
from __future__ import annotations

import httpx
import respx
from modus import Modus

SAMPLE_CONNECTION = {
    "id": "7a3f9d2c-1111-4000-a000-000000000abc",
    "name": "Production Warehouse",
    "type": "postgresql",
}


@respx.mock
def test_connections_list():
    respx.get("https://api.test/api/v1/connections").mock(
        return_value=httpx.Response(
            200,
            json={"connections": [SAMPLE_CONNECTION], "nextPageToken": None},
        ),
    )
    client = Modus(api_key="modus_test", base_url="https://api.test")
    page = client.connections.list()
    assert len(page.items) == 1
    conn = page.items[0]
    assert conn.id == SAMPLE_CONNECTION["id"]
    assert conn.name == SAMPLE_CONNECTION["name"]
    assert conn.type == SAMPLE_CONNECTION["type"]


@respx.mock
def test_connections_list_type_filter():
    route = respx.get("https://api.test/api/v1/connections").mock(
        return_value=httpx.Response(
            200,
            json={"connections": [SAMPLE_CONNECTION], "nextPageToken": None},
        ),
    )
    client = Modus(api_key="modus_test", base_url="https://api.test")
    client.connections.list(type="postgresql")
    assert route.calls[0].request.url.params["type"] == "postgresql"


@respx.mock
def test_connections_find_by_name():
    respx.get("https://api.test/api/v1/connections").mock(
        return_value=httpx.Response(
            200,
            json={"connections": [SAMPLE_CONNECTION], "nextPageToken": None},
        ),
    )
    client = Modus(api_key="modus_test", base_url="https://api.test")
    found = client.connections.find(name="production warehouse")
    assert found is not None
    assert found.id == SAMPLE_CONNECTION["id"]


@respx.mock
def test_connections_find_missing():
    respx.get("https://api.test/api/v1/connections").mock(
        return_value=httpx.Response(
            200,
            json={"connections": [SAMPLE_CONNECTION], "nextPageToken": None},
        ),
    )
    client = Modus(api_key="modus_test", base_url="https://api.test")
    assert client.connections.find(name="nonexistent") is None
