"""Regression tests: all httpx network errors must surface as ModusError, never raw httpx."""
import httpx
import pytest
import respx
from modus import Modus
from modus._exceptions import ModusError

TEST_KEY = "modus_test_key_abc123"
BASE = "https://api.modus.com"


def _client():
    return Modus(api_key=TEST_KEY, base_url=BASE)


@respx.mock
def test_read_timeout_raises_modus_error():
    respx.get(f"{BASE}/api/v1/scopes").mock(side_effect=httpx.ReadTimeout("read timed out"))
    with pytest.raises(ModusError):
        _client().scopes.list()


@respx.mock
def test_write_timeout_raises_modus_error():
    respx.get(f"{BASE}/api/v1/workflows").mock(side_effect=httpx.WriteTimeout("write timed out"))
    with pytest.raises(ModusError):
        _client().workflows.list()


@respx.mock
def test_pool_timeout_raises_modus_error():
    respx.get(f"{BASE}/api/v1/scopes").mock(side_effect=httpx.PoolTimeout("pool timed out"))
    with pytest.raises(ModusError):
        _client().scopes.list()


@respx.mock
def test_connect_error_raises_modus_error():
    """Existing behavior — ensure it still works after refactor."""
    respx.get(f"{BASE}/api/v1/scopes").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(ModusError):
        _client().scopes.list()


@respx.mock
def test_remote_protocol_error_raises_modus_error():
    respx.get(f"{BASE}/api/v1/scopes").mock(side_effect=httpx.RemoteProtocolError("bad response"))
    with pytest.raises(ModusError):
        _client().scopes.list()


@respx.mock
def test_connect_timeout_raises_modus_error():
    respx.get(f"{BASE}/api/v1/scopes").mock(side_effect=httpx.ConnectTimeout("connect timed out"))
    with pytest.raises(ModusError):
        _client().scopes.list()


@pytest.mark.asyncio
@respx.mock
async def test_read_timeout_async_raises_modus_error():
    from modus import AsyncModus
    respx.get(f"{BASE}/api/v1/scopes").mock(side_effect=httpx.ReadTimeout("read timed out"))
    async with AsyncModus(api_key=TEST_KEY, base_url=BASE) as client:
        with pytest.raises(ModusError):
            await client.scopes.list()
