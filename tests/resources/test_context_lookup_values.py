import httpx
import respx
from modus import Modus
from modus.types.context import ContextItemLookupRow

BASE = "https://api.modus.com"

LOOKUP_ROW = {
    "uid": "abc-123",
    "contextType": "metric",
    "content": {"value": 1},
    "connectionId": None,
    "selectionId": None,
    "dataPath": ["finance", "revenue"],
}


def _client():
    return Modus(api_key="modus_test_key_abc123", base_url=BASE)


@respx.mock
def test_lookup_returns_item_on_match():
    respx.post(f"{BASE}/api/v1/context/items/lookup").mock(
        return_value=httpx.Response(200, json={"item": LOOKUP_ROW})
    )
    item = _client().context.items.lookup("metric", ["finance", "revenue"])
    assert isinstance(item, ContextItemLookupRow)
    assert item.uid == "abc-123"


@respx.mock
@respx.mock
def test_lookup_returns_lean_row():
    lean = {
        "uid": "abc-123",
        "contextType": "slack_workspace_channel_list",
        "content": {"channels": []},
        "connectionId": "conn-1",
        "selectionId": "sel-1",
        "dataPath": ["ws-1", "T123"],
    }
    respx.post(f"{BASE}/api/v1/context/items/lookup").mock(
        return_value=httpx.Response(200, json={"item": lean})
    )
    item = _client().context.items.lookup("slack_workspace_channel_list", ["ws-1", "T123"])
    assert isinstance(item, ContextItemLookupRow)
    assert item.uid == "abc-123"
    assert item.connection_id == "conn-1"


@respx.mock
def test_lookup_returns_none_when_item_null():
    respx.post(f"{BASE}/api/v1/context/items/lookup").mock(
        return_value=httpx.Response(200, json={"item": None})
    )
    result = _client().context.items.lookup("metric", ["nonexistent"])
    assert result is None


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
            "values": [{"value": 123}, {"value": 456}],
            "nextPageToken": None,
        })
    )
    page = _client().context.items.list_values("abc-123", "metric", "amount")
    assert len(page) == 2
    assert page.items[0].value == 123
    assert route.called


@respx.mock
def test_lookup_sends_correct_payload():
    route = respx.post(f"{BASE}/api/v1/context/items/lookup").mock(
        return_value=httpx.Response(200, json={"item": LOOKUP_ROW})
    )
    _client().context.items.lookup(
        "metric",
        ["finance", "revenue"],
        content_projection={"fields": ["value"]},
    )
    import json

    body = json.loads(route.calls[0].request.read())
    assert body == {
        "contextType": "metric",
        "dataPath": ["finance", "revenue"],
        "contentProjection": {"fields": ["value"]},
    }
