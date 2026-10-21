"""Tests for mgmt.scopes.memories()."""

import json

import httpx
import pytest
import respx
from modus.management.types.memories import (
    Memory,
    MemorySearchRequest,
    MemorySearchResult,
    MemoryUpdate,
)
from modus.types.pagination import Page

BASE = "https://api.modus.com"
SKILL_ID = 42
MEMORIES_BASE = f"{BASE}/api/v1/scopes/{SKILL_ID}/memories"

SAMPLE_MEMORY = {
    "id": "mem_01",
    "memory": "User prefers bullet points.",
    "hash": "abc123",
    "metadata": {"source": "chat"},
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-02T00:00:00.000Z",
}


@respx.mock
def test_memories_list(client) -> None:
    route = respx.get(MEMORIES_BASE).mock(
        return_value=httpx.Response(
            200,
            json={
                "memories": [SAMPLE_MEMORY],
                "nextPageToken": "page-2",
            },
        )
    )
    page = client.scopes.memories(SKILL_ID).list(page_size=25, page_token="tok_abc")
    assert isinstance(page, Page)
    assert len(page) == 1
    item = page.items[0]
    assert isinstance(item, Memory)
    assert item.id == "mem_01"
    assert item.memory == "User prefers bullet points."
    assert page.next_page_token == "page-2"
    params = dict(route.calls[0].request.url.params)
    assert params["pageSize"] == "25"
    assert params["pageToken"] == "tok_abc"


@respx.mock
def test_memories_list_user_id(client) -> None:
    route = respx.get(MEMORIES_BASE).mock(
        return_value=httpx.Response(
            200,
            json={"memories": [], "nextPageToken": None},
        )
    )
    client.scopes.memories(SKILL_ID).list(page_size=10, user_id="user-abc")
    assert route.called
    assert dict(route.calls[0].request.url.params)["userId"] == "user-abc"


@respx.mock
def test_memories_search(client) -> None:
    route = respx.post(f"{MEMORIES_BASE}/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "memories": [SAMPLE_MEMORY],
                "nextPageToken": None,
            },
        )
    )
    result = client.scopes.memories(SKILL_ID).search(
        MemorySearchRequest(query="revenue preferences", limit=5)
    )
    assert isinstance(result, MemorySearchResult)
    assert len(result.memories) == 1
    assert result.memories[0].id == "mem_01"
    body = json.loads(route.calls[0].request.read())
    assert body["query"] == "revenue preferences"
    assert body["limit"] == 5


@respx.mock
def test_memories_update(client) -> None:
    route = respx.patch(f"{MEMORIES_BASE}/mem_01").mock(
        return_value=httpx.Response(200, json={**SAMPLE_MEMORY, "memory": "Updated text."})
    )
    memory = client.scopes.memories(SKILL_ID).update(
        "mem_01",
        MemoryUpdate.text_only("Updated text."),
    )
    assert isinstance(memory, Memory)
    assert memory.memory == "Updated text."
    body = json.loads(route.calls[0].request.read())
    assert body == {"memory": "Updated text."}


@respx.mock
def test_memories_update_with_mask(client) -> None:
    route = respx.patch(f"{MEMORIES_BASE}/mem_01?updateMask=memory").mock(
        return_value=httpx.Response(200, json=SAMPLE_MEMORY)
    )
    client.scopes.memories(SKILL_ID).update(
        "mem_01",
        MemoryUpdate.text_only("Only memory field."),
        update_mask="memory",
    )
    assert route.called
    assert "updateMask=memory" in str(route.calls[0].request.url)


@respx.mock
def test_memories_update_rejects_empty_memory_id(client) -> None:
    with pytest.raises(ValueError, match="memory_id"):
        client.scopes.memories(SKILL_ID).update("  ", MemoryUpdate.text_only("x"))


@respx.mock
def test_memories_list_rejects_empty_scope_id(client) -> None:
    with pytest.raises(ValueError, match="scope_id"):
        client.scopes.memories("").list()
    assert not respx.calls


@respx.mock
async def test_async_memories_list_rejects_empty_scope_id(async_client) -> None:
    with pytest.raises(ValueError, match="scope_id"):
        await async_client.scopes.memories("").list()
    assert not respx.calls


@respx.mock
def test_memories_delete(client) -> None:
    route = respx.delete(f"{MEMORIES_BASE}/mem_01").mock(
        return_value=httpx.Response(204)
    )
    client.scopes.memories(SKILL_ID).delete("mem_01")
    assert route.called
