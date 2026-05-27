import httpx
import pytest
import respx
from modus import Modus
from modus.types.context import ContextItem

BASE = "https://api.modus.com"

ITEM = {
    "uid": "abc-123", "contextType": "metric",
    "title": "Revenue", "description": None, "content": None,
    "verificationStatus": "verified", "userFeedback": None,
    "topics": [], "connectionId": None, "updateSource": "manual",
    "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z",
}


def _client():
    return Modus(api_key="modus_test_key_abc123", base_url=BASE)


@respx.mock
def test_lookup_returns_item_on_match():
    respx.post(f"{BASE}/api/v1/context/items/lookup").mock(
        return_value=httpx.Response(200, json=ITEM)
    )
    item = _client().context.items.lookup("metric", ["finance", "revenue"])
    assert isinstance(item, ContextItem)
    assert item.uid == "abc-123"


@respx.mock
def test_lookup_returns_none_on_404():
    respx.post(f"{BASE}/api/v1/context/items/lookup").mock(
        return_value=httpx.Response(404, json={"message": "Not found"})
    )
    result = _client().context.items.lookup("metric", ["nonexistent"])
    assert result is None


@respx.mock
def test_list_values_returns_page():
    route = respx.get(f"{BASE}/api/v1/context/items/abc-123/values").mock(
        return_value=httpx.Response(200, json={
            "items": [{"value": 123}, {"value": 456}],
            "nextCursor": None,
        })
    )
    page = _client().context.items.list_values("abc-123", "metric", "amount")
    assert len(page) == 2
    assert page.items[0] == {"value": 123}
    # Verify required query params are sent correctly
    assert route.calls[0].request.url.params["contextType"] == "metric"
    assert route.calls[0].request.url.params["contentKeyPath"] == "amount"


@respx.mock
def test_lookup_sends_correct_payload():
    route = respx.post(f"{BASE}/api/v1/context/items/lookup").mock(
        return_value=httpx.Response(200, json=ITEM)
    )
    _client().context.items.lookup("metric", ["finance", "revenue"])
    import json
    body = json.loads(route.calls[0].request.read())
    assert body == {"contextType": "metric", "dataPath": ["finance", "revenue"]}
