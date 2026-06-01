"""Tests for context items read operations."""


import httpx
import pytest
import respx
from modus import NotFoundError
from modus.types.context import ContextItem

BASE = "https://api.modus.com"


@respx.mock
def test_context_item_title_is_optional(client):
    """Integration-synced items (bigquery, slack, github, etc.) omit title.
    ContextItem.title must be Optional[str] — a missing title must not raise."""
    item_without_title = {
        "uid": "integration-item-uid",
        "contextType": "bigquery_table",
        # no "title" field at all
        "description": "Some BigQuery table",
        "content": None,
        "verificationStatus": "unverified",
        "userFeedback": None,
        "topics": [],
        "connectionId": "conn-uuid",
        "updateSource": "integration",
        "createdAt": "2026-01-01T00:00:00.000Z",
        "updatedAt": "2026-01-01T00:00:00.000Z",
    }
    respx.get(f"{BASE}/api/v1/context/items").mock(
        return_value=httpx.Response(200, json={
            "contextItems": [item_without_title],
            "nextPageToken": None,
        })
    )
    page = client.context.items.list()
    assert len(page) == 1
    item = page.items[0]
    assert isinstance(item, ContextItem)
    assert item.title is None
    assert item.description == "Some BigQuery table"
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
def test_context_items_get(client, sample_context_item):
    uid = sample_context_item["uid"]
    respx.get(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json=sample_context_item)
    )
    item = client.context.items.get(uid)
    assert item.title == "Fiscal Year Definition"
    assert item.verification_status == "verified"


@respx.mock
def test_context_items_get_not_found(client):
    respx.get(f"{BASE}/api/v1/context/items/no-such-uid").mock(
        return_value=httpx.Response(404, json={"message": "Not found"})
    )
    with pytest.raises(NotFoundError):
        client.context.items.get("no-such-uid")
