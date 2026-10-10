"""Tests for context items read operations."""


import httpx
import pytest
import respx
from modus import NotFoundError
from modus.types.context import ContextItem

BASE = "https://api.modus.com"


@respx.mock
def test_context_item_description_is_optional(client):
    """Integration-synced items may omit description."""
    item_without_description = {
        "uid": "integration-item-uid",
        "orgId": "org-uuid-abc",
        "contextType": "bigquery_table",
        "description": None,
        "content": {},
        "userFeedback": "neutral",
        "topics": [],
        "connectionId": "conn-uuid",
        "selectionId": None,
        "dataPath": ["bigquery", "dataset", "table"],
        "createdAt": "2026-01-01T00:00:00.000Z",
        "updatedAt": "2026-01-01T00:00:00.000Z",
    }
    respx.get(f"{BASE}/api/v1/context/items").mock(
        return_value=httpx.Response(200, json={
            "contextItems": [item_without_description],
            "nextPageToken": None,
        })
    )
    page = client.context.items.list()
    assert len(page) == 1
    item = page.items[0]
    assert isinstance(item, ContextItem)
    assert item.description is None
    assert item.context_type == "bigquery_table"


@respx.mock
def test_context_items_list(client, sample_context_item):
    respx.get(f"{BASE}/api/v1/context/items").mock(
        return_value=httpx.Response(200, json={
            "contextItems": [sample_context_item],
            "nextPageToken": None,
        })
    )
    page = client.context.items.list()
    assert len(page) == 1
    item = page.items[0]
    assert isinstance(item, ContextItem)
    assert item.uid == "7a3f9d2c-1111-4000-a000-000000000abc"
    assert item.context_type == "note"


@respx.mock
def test_context_items_list_filter_by_type(client):
    route = respx.get(f"{BASE}/api/v1/context/items").mock(
        return_value=httpx.Response(200, json={"contextItems": [], "nextPageToken": None})
    )
    client.context.items.list(context_type="metric")
    url = str(route.calls[0].request.url)
    assert "contextTypes=metric" in url
    assert "pageSize=" in url


@respx.mock
def test_context_items_list_browse_selectors(client):
    route = respx.get(f"{BASE}/api/v1/context/items").mock(
        return_value=httpx.Response(200, json={"contextItems": [], "nextPageToken": None})
    )
    client.context.items.list(
        parent_uids=[],
        ancestor_uids=["native-folder"],
        connection_ids=["files", "conn-a"],
    )
    params = route.calls[0].request.url.params
    assert params.get_list("parentUids") == [""]
    assert params.get_list("ancestorUids") == ["native-folder"]
    assert params.get_list("connectionIds") == ["files", "conn-a"]
    assert "parentUid" not in params
    assert "ancestorUid" not in params

    client.context.items.list(context_type="note")
    omitted = route.calls[1].request.url
    assert "parentUids" not in omitted.params
    assert "ancestorUids" not in omitted.params
    assert "connectionIds" not in omitted.params
    assert "contextTypes" in omitted.params


@respx.mock
def test_context_items_list_preserves_native_uid_order_and_whitespace(client):
    route = respx.get(f"{BASE}/api/v1/context/items").mock(
        return_value=httpx.Response(200, json={"contextItems": [], "nextPageToken": None})
    )
    long_uid = "native " + ("x" * 260)
    client.context.items.list(parent_uids=["db-a", " PUBLIC ", long_uid])
    assert route.calls[0].request.url.params.get_list("parentUids") == [
        "db-a",
        " PUBLIC ",
        long_uid,
    ]


@respx.mock
def test_context_items_get(client, sample_context_item):
    uid = sample_context_item["uid"]
    respx.get(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json=sample_context_item)
    )
    item = client.context.items.get(uid)
    assert item.description == "Defines the company fiscal year"
    assert item.user_feedback == "positive"


@respx.mock
def test_context_items_get_not_found(client):
    respx.get(f"{BASE}/api/v1/context/items/no-such-uid").mock(
        return_value=httpx.Response(404, json={"message": "Not found"})
    )
    with pytest.raises(NotFoundError):
        client.context.items.get("no-such-uid")
