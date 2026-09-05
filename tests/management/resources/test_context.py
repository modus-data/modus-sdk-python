"""Tests for mgmt.context.* (create + items CRUD)."""

import json

import httpx
import pytest
import respx
from modus.management import ModusManagement
from modus.management.types.context import (
    ContextItem,
    ContextItemDeletion,
    CreatedContextItem,
)
from tests.fixtures.context_content import (
    LINK_CONTENT,
    NOTE_CONTENT,
    SAVED_QUERY_CONTENT,
)

BASE = "https://api.modus.com"


def _context_item_wire(uid: str, context_type: str, content: dict) -> dict:
    return {
        "uid": uid,
        "orgId": "org-uuid-abc",
        "contextType": context_type,
        "description": "Defines the company fiscal year",
        "content": content,
        "userFeedback": "neutral",
        "topics": [],
        "connectionId": None,
        "selectionId": None,
        "dataPath": [],
        "createdAt": "2026-01-01T00:00:00.000Z",
        "updatedAt": "2026-01-01T00:00:00.000Z",
    }


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
        return_value=httpx.Response(
            200, json={"contextItems": [sample_context_item], "nextPageToken": None}
        )
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
    updated = {**sample_context_item, "description": "Reviewed"}
    patch_route = respx.patch(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json={"uid": uid})
    )
    respx.get(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json=updated)
    )
    item = client.context.items.update(
        uid,
        description="Reviewed",
        user_feedback="positive",
        topics=["analytics"],
    )
    assert item.description == "Reviewed"
    # Body must match the API contract — only whitelisted fields, camelCased.
    body = json.loads(patch_route.calls[0].request.read())
    assert body == {
        "description": "Reviewed",
        "userFeedback": "positive",
        "topics": ["analytics"],
    }
    assert "title" not in body and "verificationStatus" not in body


@respx.mock
def test_context_items_update_clears_field_via_mask(client, sample_context_item):
    uid = "7a3f9d2c-1111-4000-a000-000000000abc"
    patch_route = respx.patch(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json={"uid": uid})
    )
    respx.get(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json=sample_context_item)
    )
    # Name the field in the mask and leave it unset → server sets it to null.
    client.context.items.update(uid, update_mask="description")
    req = patch_route.calls[0].request
    assert req.url.params["updateMask"] == "description"
    body = json.loads(req.read())
    assert "description" in body and body["description"] is None


@respx.mock
def test_context_items_delete(client):
    uid = "7a3f9d2c-1111-4000-a000-000000000abc"
    respx.delete(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json={"uid": uid, "contextType": "note"})
    )
    result = client.context.items.delete(uid)
    assert isinstance(result, ContextItemDeletion)
    assert result.uid == uid


@respx.mock
def test_custom_context_items_create(client):
    route = respx.post(f"{BASE}/api/v1/context/custom-items").mock(
        return_value=httpx.Response(
            201,
            json={
                "contextItemId": "custom-1",
                "contextType": "custom_entity_metadata",
                "dataPath": ["billing-db", "contracts", "contract-123"],
                "title": "Acme renewal",
            },
        )
    )
    result = client.context.custom_items.create(
        kind="entity",
        source_id="billing-db",
        collection_id="contracts",
        external_id="contract-123",
        name="Acme renewal",
    )

    assert result["contextItemId"] == "custom-1"
    body = json.loads(route.calls[0].request.read())
    assert body == {
        "kind": "entity",
        "sourceId": "billing-db",
        "collectionId": "contracts",
        "externalId": "contract-123",
        "name": "Acme renewal",
    }


@respx.mock
def test_custom_context_item_relations_create(client):
    route = respx.post(f"{BASE}/api/v1/context/custom-items/relations").mock(
        return_value=httpx.Response(201, json={"upsertedCount": 1})
    )

    count = client.context.custom_items.create_relations(
        [
            {
                "from_uid": "source-1",
                "to_uid": "target-1",
                "relation_type": "depends_on",
                "content": {"source": "go.mod"},
            }
        ]
    )

    assert count == 1
    assert json.loads(route.calls[0].request.read()) == {
        "relations": [
            {
                "fromUid": "source-1",
                "toUid": "target-1",
                "relationType": "depends_on",
                "content": {"source": "go.mod"},
            }
        ]
    }


@pytest.mark.asyncio
@respx.mock
async def test_custom_context_item_relations_create_async(async_client):
    respx.post(f"{BASE}/api/v1/context/custom-items/relations").mock(
        return_value=httpx.Response(201, json={"upsertedCount": 1})
    )

    count = await async_client.context.custom_items.create_relations(
        [{"from_uid": "source-1", "to_uid": "target-1", "relation_type": "depends_on"}]
    )

    assert count == 1


@respx.mock
def test_custom_context_items_list(client):
    route = respx.get(f"{BASE}/api/v1/context/custom-items").mock(
        return_value=httpx.Response(
            200, json={"contextItems": [], "nextPageToken": None}
        )
    )
    page = client.context.custom_items.list(topics=["billing"])

    assert len(page) == 0
    assert route.calls[0].request.url.params["topics"] == "billing"


@respx.mock
def test_custom_context_items_update_and_delete(client):
    uid = "custom-1"
    patch_route = respx.patch(f"{BASE}/api/v1/context/custom-items/{uid}").mock(
        return_value=httpx.Response(200, json={"uid": uid})
    )
    delete_route = respx.delete(f"{BASE}/api/v1/context/custom-items/{uid}").mock(
        return_value=httpx.Response(
            200, json={"uid": uid, "contextType": "custom_entity_metadata"}
        )
    )

    client.context.custom_items.update(uid, description="Reviewed", topics=["billing"])
    deleted = client.context.custom_items.delete(uid)

    body = json.loads(patch_route.calls[0].request.read())
    assert body == {"description": "Reviewed", "topics": ["billing"]}
    assert delete_route.called
    assert deleted.context_type == "custom_entity_metadata"


@respx.mock
def test_context_update_note_merges_content(client):
    uid = "note-id-001"
    wire = _context_item_wire(uid, "note", NOTE_CONTENT)
    patch_route = respx.patch(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json={"uid": uid})
    )
    respx.get(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json=wire)
    )
    client.context.update_note(uid, title="Updated title", body="New body.")
    body = json.loads(patch_route.calls[0].request.read())
    assert body["contextType"] == "note"
    assert body["content"]["title"] == "Updated title"
    assert body["content"]["content"] == "New body."
    assert body["content"]["noteId"] == NOTE_CONTENT["noteId"]
    assert body["content"]["s3Key"] == NOTE_CONTENT["s3Key"]


@respx.mock
def test_context_update_note_uses_existing_to_skip_get(client):
    uid = "note-id-001"
    wire = _context_item_wire(uid, "note", NOTE_CONTENT)
    existing = ContextItem.model_validate(wire)
    patch_route = respx.patch(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json={"uid": uid})
    )
    respx.get(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json=wire)
    )
    client.context.update_note(
        uid,
        title="Updated title",
        body="New body.",
        existing=existing,
    )
    assert len(respx.calls) == 2  # patch + post-update get
    body = json.loads(patch_route.calls[0].request.read())
    assert body["content"]["noteId"] == NOTE_CONTENT["noteId"]


@respx.mock
def test_context_update_link_merges_metadata(client):
    uid = "link-id-001"
    wire = _context_item_wire(uid, "link", LINK_CONTENT)
    patch_route = respx.patch(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json={"uid": uid})
    )
    respx.get(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json=wire)
    )
    client.context.update_link(uid, title="Renamed link")
    body = json.loads(patch_route.calls[0].request.read())
    assert body["contextType"] == "link"
    assert body["content"]["title"] == "Renamed link"
    assert body["content"]["linkId"] == LINK_CONTENT["linkId"]


@respx.mock
def test_context_update_saved_query_merges_content(client):
    uid = "query-id-001"
    wire = _context_item_wire(uid, "saved_query", SAVED_QUERY_CONTENT)
    patch_route = respx.patch(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json={"uid": uid})
    )
    respx.get(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json=wire)
    )
    client.context.update_saved_query(
        uid,
        name="Renamed query",
        query="SELECT 1",
        connection_id="conn-002",
    )
    body = json.loads(patch_route.calls[0].request.read())
    assert body["contextType"] == "saved_query"
    assert body["content"]["name"] == "Renamed query"
    assert body["content"]["query"] == "SELECT 1"
    assert body["content"]["connectionId"] == "conn-002"
    assert body["content"]["queryId"] == SAVED_QUERY_CONTENT["queryId"]
