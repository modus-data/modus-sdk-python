"""Regression: path ids that do not address one resource are rejected before any request.

URL normalisation drops dot segments and Express routes a trailing slash to the
list route, so these ids silently targeted another resource:
``scopes.memories(7).delete('..')`` sent ``DELETE /api/v1/scopes/7`` and deleted the scope.
"""
import pytest
from modus import AsyncModus, Modus
from modus.management import ModusManagement

BASE = "https://api.modus.com"
KEY = "modus_test_key_path"
BAD_IDS = ["", "  ", ".", ".."]


@pytest.mark.parametrize("bad", BAD_IDS)
def test_get_rejects_bad_id(bad, respx_mock):
    with pytest.raises(ValueError):
        Modus(api_key=KEY, base_url=BASE).context.items.get(bad)
    assert respx_mock.calls.call_count == 0


@pytest.mark.parametrize("bad", BAD_IDS)
def test_delete_rejects_bad_id(bad, respx_mock):
    with pytest.raises(ValueError):
        ModusManagement(api_key=KEY, base_url=BASE).scopes.memories(7).delete(bad)
    assert respx_mock.calls.call_count == 0


@pytest.mark.parametrize("bad", BAD_IDS)
async def test_async_get_rejects_bad_id(bad, respx_mock):
    with pytest.raises(ValueError):
        await AsyncModus(api_key=KEY, base_url=BASE).context.items.get(bad)
    assert respx_mock.calls.call_count == 0


@pytest.mark.parametrize("bad", [".", ".."])
def test_chat_rejects_dot_thread_id(bad, respx_mock):
    with pytest.raises(ValueError):
        Modus(api_key=KEY, base_url=BASE).scopes.chat(7, "hi", model="claude-sonnet-5", thread_id=bad)
    assert respx_mock.calls.call_count == 0
