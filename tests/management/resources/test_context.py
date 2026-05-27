"""Tests for mgmt.context.* (create + items CRUD)."""

import json
import httpx
import respx
from modus.management import ModusManagement
from modus.management.types.context import ContextItem, ContextItemDeletion, CreatedContextItem

BASE = "https://api.modus.com"

CREATED_RESP = {
    "contextItemId": "uid-abc-123",
    "kind": "note",
    "title": "Fiscal Year",
    "s3Key": "org/notes/uid-abc-123.json",
}


def _client():
    return ModusManagement(api_key="modus_test_key", base_url=BASE)


@respx.mock
def test_context_create_note():
    route = respx.post(f"{BASE}/api/v1/context/notes").mock(
        return_value=httpx.Response(201, json=CREATED_RESP)
    )
    result = _client().context.create_note("Fiscal Year", "Feb 1 – Jan 31.")
    assert isinstance(result, CreatedContextItem)
    assert result.context_item_id == "uid-abc-123"
    assert result.kind == "note"
    body = json.loads(route.calls[0].request.read())
    assert body["title"] == "Fiscal Year"


@respx.mock
def test_context_create_saved_query():
    route = respx.post(f"{BASE}/api/v1/context/saved-queries").mock(
        return_value=httpx.Response(201, json={**CREATED_RESP, "kind": "saved_query"})
    )
    _client().context.create_saved_query(
        "Top Customers",
        "SELECT id FROM customers LIMIT 10",
        connection_id="conn-001",
    )
    body = json.loads(route.calls[0].request.read())
    assert body["name"] == "Top Customers"
    assert body["connectionId"] == "conn-001"


@respx.mock
def test_context_items_list(client, sample_context_item):
    respx.get(f"{BASE}/api/v1/context/items").mock(
        return_value=httpx.Response(200, json={"items": [sample_context_item], "nextCursor": None})
    )
    page = client.context.items.list()
    assert len(page) == 1
    item = page.items[0]
    assert isinstance(item, ContextItem)
    assert item.uid == "7a3f9d2c-1111-4000-a000-000000000abc"


@respx.mock
def test_context_items_get(client, sample_context_item):
    uid = "7a3f9d2c-1111-4000-a000-000000000abc"
    respx.get(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json=sample_context_item)
    )
    item = client.context.items.get(uid)
    assert item.uid == uid
    assert item.context_type == "note"


@respx.mock
def test_context_items_update(client, sample_context_item):
    uid = "7a3f9d2c-1111-4000-a000-000000000abc"
    updated = {**sample_context_item, "title": "Updated Title"}
    respx.patch(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json=updated)
    )
    respx.get(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json=updated)
    )
    item = client.context.items.update(uid, title="Updated Title")
    assert item.title == "Updated Title"


@respx.mock
def test_context_items_delete(client):
    uid = "7a3f9d2c-1111-4000-a000-000000000abc"
    respx.delete(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json={"uid": uid, "contextType": "note"})
    )
    result = client.context.items.delete(uid)
    assert isinstance(result, ContextItemDeletion)
    assert result.uid == uid
