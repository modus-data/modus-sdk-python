"""Regression: delete() must return body when present, None on 204."""
import httpx
import pytest
import respx
from modus._config import ModusConfig
from modus._http import AsyncHttpClient, HttpClient

BASE = "https://api.modus.com"
CFG = ModusConfig(api_key="modus_test", base_url=BASE)


def test_delete_returns_none_on_204():
    with respx.mock:
        respx.delete(f"{BASE}/test").mock(return_value=httpx.Response(204))
        result = HttpClient(CFG).delete("/test")
        assert result is None


def test_delete_returns_body_on_200():
    with respx.mock:
        respx.delete(f"{BASE}/test").mock(
            return_value=httpx.Response(200, json={"uid": "abc", "contextType": "note"})
        )
        result = HttpClient(CFG).delete("/test")
        assert result == {"uid": "abc", "contextType": "note"}


def test_delete_returns_none_on_200_empty_body():
    with respx.mock:
        respx.delete(f"{BASE}/test").mock(return_value=httpx.Response(200, content=b""))
        result = HttpClient(CFG).delete("/test")
        assert result is None


@pytest.mark.asyncio
async def test_async_delete_returns_body_on_200():
    with respx.mock:
        respx.delete(f"{BASE}/test").mock(
            return_value=httpx.Response(200, json={"uid": "xyz", "contextType": "metric"})
        )
        result = await AsyncHttpClient(CFG).delete("/test")
        assert result == {"uid": "xyz", "contextType": "metric"}
