"""
Async parity tests: every sync read method has an async equivalent that
works correctly. Uses respx async mocking.
"""
import httpx
import pytest
import respx
from modus import AsyncModus
from modus.types.context import ContextItem

BASE = "https://api.modus.com"
KEY = "modus_test_key_abc123"

ITEM_RESP = {
    "uid": "abc", "contextType": "note",
    "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z",
}


@pytest.mark.asyncio
@respx.mock
async def test_async_context_lookup_returns_none_on_404():
    respx.post(f"{BASE}/api/v1/context/items/lookup").mock(
        return_value=httpx.Response(404, json={"message": "Not found"})
    )
    async with AsyncModus(api_key=KEY, base_url=BASE) as client:
        result = await client.context.items.lookup("metric", ["nonexistent"])
    assert result is None
