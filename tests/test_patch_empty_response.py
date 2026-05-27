"""Regression: patch() must not crash on 204 or empty body."""
import httpx
import pytest
import respx
from modus._http import HttpClient, AsyncHttpClient
from modus._config import ModusConfig

BASE = "https://api.modus.com"
CFG = ModusConfig(api_key="modus_test", base_url=BASE)


def test_patch_returns_none_on_204():
    with respx.mock:
        respx.patch(f"{BASE}/test").mock(return_value=httpx.Response(204))
        result = HttpClient(CFG).patch("/test", json={"x": 1})
        assert result is None


def test_patch_returns_none_on_200_empty_body():
    with respx.mock:
        respx.patch(f"{BASE}/test").mock(return_value=httpx.Response(200, content=b""))
        result = HttpClient(CFG).patch("/test", json={"x": 1})
        assert result is None


def test_patch_returns_json_on_200_with_body():
    with respx.mock:
        respx.patch(f"{BASE}/test").mock(return_value=httpx.Response(200, json={"id": 42}))
        result = HttpClient(CFG).patch("/test", json={"x": 1})
        assert result == {"id": 42}


@pytest.mark.asyncio
async def test_async_patch_returns_none_on_204():
    with respx.mock:
        respx.patch(f"{BASE}/test").mock(return_value=httpx.Response(204))
        result = await AsyncHttpClient(CFG).patch("/test", json={"x": 1})
        assert result is None
