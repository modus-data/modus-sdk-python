"""Tests for client.skills.conversations.list() and .get()."""

import httpx
import pytest
import respx
from modus.types.conversations import Conversation, ConversationListItem

BASE = "https://api.modus.com"


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_list_item(i: int = 0) -> dict:
    """Matches the real ConversationListItem shape from the API list endpoint."""
    return {
        "threadId": f"thread-{i}",
        "skillId": 42,
        "firstMessage": f"Hello from thread {i}",
        "title": None,
        "messageCount": 5,
        "createdAt": "2026-01-01T00:00:00.000Z",
        "updatedAt": "2026-01-01T00:00:00.000Z",
        "userIds": ["user-abc"],
    }


def make_conversation() -> dict:
    """Matches the real Conversation shape from the API get endpoint."""
    return {
        "threadId": "thread-abc",
        "skillId": 42,
        "messages": [
            {"type": "human", "content": "Hello"},
            {"type": "ai", "content": "Hi there!", "toolCalls": []},
        ],
        "createdAt": "2026-01-01T00:00:00.000Z",
        "updatedAt": "2026-01-01T00:00:00.000Z",
    }


# ── Validation ────────────────────────────────────────────────────────────────

def test_conversations_list_rejects_invalid_page(client):
    with pytest.raises(ValueError, match="page must be >= 1"):
        client.skills.conversations.list(42, page=0)


def test_conversations_list_rejects_invalid_page_size(client):
    with pytest.raises(ValueError, match="page_size must be >= 1"):
        client.skills.conversations.list(42, page_size=0)


# ── List ──────────────────────────────────────────────────────────────────────

@respx.mock
def test_conversations_list_returns_list_items(client):
    """list() returns ConversationListItem, not full Conversation objects."""
    respx.get(f"{BASE}/api/v1/skills/42/conversations").mock(
        return_value=httpx.Response(200, json={
            "items": [make_list_item(0)],
            "totalCount": 1,
            "page": 0,
            "pageSize": 20,
        })
    )
    page = client.skills.conversations.list(42)
    assert len(page) == 1
    item = page.items[0]
    assert isinstance(item, ConversationListItem)
    assert item.thread_id == "thread-0"
    assert item.first_message == "Hello from thread 0"
    assert item.message_count == 5
    assert item.user_ids == ["user-abc"]
    assert item.title is None


@respx.mock
def test_conversations_list_sends_zero_based_page_to_api(client):
    """SDK page is 1-based; the API receives 0-based. Page 1 → sends page=0."""
    route = respx.get(f"{BASE}/api/v1/skills/42/conversations").mock(
        return_value=httpx.Response(200, json={
            "items": [], "totalCount": 0, "page": 0, "pageSize": 20,
        })
    )
    client.skills.conversations.list(42)  # default page=1
    params = route.calls[0].request.url.params
    assert params["page"] == "0", "page=1 (SDK) must map to page=0 (API)"


@respx.mock
def test_conversations_list_page_offset_conversion(client):
    """SDK page=3 must send page=2 to the API (0-based)."""
    route = respx.get(f"{BASE}/api/v1/skills/42/conversations").mock(
        return_value=httpx.Response(200, json={
            "items": [], "totalCount": 0, "page": 2, "pageSize": 10,
        })
    )
    client.skills.conversations.list(42, page=3, page_size=10)
    params = route.calls[0].request.url.params
    assert params["page"] == "2"
    assert params["pageSize"] == "10"


@respx.mock
def test_conversations_list_has_next_page(client):
    """has_next_page is True when page * page_size < totalCount."""
    respx.get(f"{BASE}/api/v1/skills/42/conversations").mock(
        return_value=httpx.Response(200, json={
            "items": [make_list_item(i) for i in range(5)],
            "totalCount": 12,
            "page": 0,
            "pageSize": 5,
        })
    )
    page = client.skills.conversations.list(42, page_size=5)
    assert page.has_next_page() is True


@respx.mock
def test_conversations_list_no_next_page(client):
    respx.get(f"{BASE}/api/v1/skills/42/conversations").mock(
        return_value=httpx.Response(200, json={
            "items": [],
            "totalCount": 3,
            "page": 0,
            "pageSize": 20,
        })
    )
    page = client.skills.conversations.list(42)
    assert page.has_next_page() is False


@respx.mock
def test_conversations_auto_paging_iter(client):
    """auto_paging_iter walks offset pages transparently."""
    respx.get(f"{BASE}/api/v1/skills/42/conversations").mock(side_effect=[
        httpx.Response(200, json={
            "items": [make_list_item(0), make_list_item(1)],
            "totalCount": 4,
            "page": 0,
            "pageSize": 2,
        }),
        httpx.Response(200, json={
            "items": [make_list_item(2), make_list_item(3)],
            "totalCount": 4,
            "page": 1,
            "pageSize": 2,
        }),
    ])

    page = client.skills.conversations.list(42, page_size=2)
    all_threads = list(page.auto_paging_iter())
    assert len(all_threads) == 4
    assert all_threads[0].thread_id == "thread-0"
    assert all_threads[3].thread_id == "thread-3"


# ── Get ───────────────────────────────────────────────────────────────────────

@respx.mock
def test_conversations_get(client):
    """get() returns a full Conversation with messages using type not role."""
    respx.get(f"{BASE}/api/v1/skills/42/conversations/thread-abc").mock(
        return_value=httpx.Response(200, json=make_conversation())
    )
    conv = client.skills.conversations.get(42, "thread-abc")
    assert isinstance(conv, Conversation)
    assert conv.thread_id == "thread-abc"
    assert len(conv.messages) == 2
    assert conv.messages[0].type == "human"
    assert conv.messages[0].content == "Hello"
    assert conv.messages[1].type == "ai"
    assert conv.messages[1].content == "Hi there!"


@respx.mock
def test_conversations_get_with_tool_calls(client):
    """Messages with toolCalls are parsed correctly."""
    respx.get(f"{BASE}/api/v1/skills/42/conversations/thread-tools").mock(
        return_value=httpx.Response(200, json={
            "threadId": "thread-tools",
            "skillId": 42,
            "messages": [
                {"type": "human", "content": "Run a query"},
                {
                    "type": "ai",
                    "content": "",
                    "toolCalls": [
                        {"name": "sql_query", "args": {"sql": "SELECT 1"}, "id": "tc-1", "type": "tool_call"}
                    ],
                },
            ],
            "createdAt": "2026-01-01T00:00:00.000Z",
            "updatedAt": "2026-01-01T00:00:00.000Z",
        })
    )
    conv = client.skills.conversations.get(42, "thread-tools")
    ai_msg = conv.messages[1]
    assert ai_msg.tool_calls is not None
    assert len(ai_msg.tool_calls) == 1
    assert ai_msg.tool_calls[0]["name"] == "sql_query"
