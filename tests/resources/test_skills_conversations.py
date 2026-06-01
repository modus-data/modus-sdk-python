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

def test_conversations_list_rejects_invalid_page_size(client):
    with pytest.raises(ValueError, match="page_size must be a positive int"):
        client.skills.conversations.list(42, page_size=0)


# ── List ──────────────────────────────────────────────────────────────────────

@respx.mock
def test_conversations_list_returns_list_items(client):
    """list() returns ConversationListItem, not full Conversation objects."""
    respx.get(f"{BASE}/api/v1/skills/42/conversations").mock(
        return_value=httpx.Response(200, json={
            "conversations": [make_list_item(0)],
            "nextPageToken": None,
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
def test_conversations_list_sends_aip_params(client):
    """First page sends pageSize only; pageToken omitted."""
    route = respx.get(f"{BASE}/api/v1/skills/42/conversations").mock(
        return_value=httpx.Response(200, json={
            "conversations": [],
            "nextPageToken": None,
        })
    )
    client.skills.conversations.list(42, page_size=25)
    params = route.calls[0].request.url.params
    assert params["pageSize"] == "25"
    assert "pageToken" not in params
    assert "page" not in params


@respx.mock
def test_conversations_list_sends_page_token(client):
    route = respx.get(f"{BASE}/api/v1/skills/42/conversations").mock(
        return_value=httpx.Response(200, json={
            "conversations": [],
            "nextPageToken": None,
        })
    )
    client.skills.conversations.list(42, page_size=10, page_token="tok_abc")
    params = route.calls[0].request.url.params
    assert params["pageSize"] == "10"
    assert params["pageToken"] == "tok_abc"


@respx.mock
def test_conversations_list_has_next_page(client):
    respx.get(f"{BASE}/api/v1/skills/42/conversations").mock(
        return_value=httpx.Response(200, json={
            "conversations": [make_list_item(i) for i in range(2)],
            "nextPageToken": "tok_next",
        })
    )
    page = client.skills.conversations.list(42, page_size=2)
    assert page.has_next_page() is True
    assert page.next_page_token == "tok_next"


@respx.mock
def test_conversations_list_no_next_page(client):
    respx.get(f"{BASE}/api/v1/skills/42/conversations").mock(
        return_value=httpx.Response(200, json={
            "conversations": [],
            "nextPageToken": None,
        })
    )
    page = client.skills.conversations.list(42)
    assert page.has_next_page() is False


@respx.mock
def test_conversations_auto_paging_iter(client):
    """auto_paging_iter follows nextPageToken."""
    respx.get(f"{BASE}/api/v1/skills/42/conversations").mock(side_effect=[
        httpx.Response(200, json={
            "conversations": [make_list_item(0), make_list_item(1)],
            "nextPageToken": "tok_p2",
        }),
        httpx.Response(200, json={
            "conversations": [make_list_item(2), make_list_item(3)],
            "nextPageToken": None,
        }),
    ])

    page = client.skills.conversations.list(42, page_size=2)
    all_threads = list(page.auto_paging_iter())
    assert len(all_threads) == 4
    assert all_threads[0].thread_id == "thread-0"
    assert all_threads[3].thread_id == "thread-3"
    assert respx.calls.call_count == 2
    assert respx.calls[1].request.url.params["pageToken"] == "tok_p2"


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
    tc = ai_msg.tool_calls[0]
    assert tc.name == "sql_query"
    assert tc.id == "tc-1"
    assert tc.type == "tool_call"
    assert tc.args == {"sql": "SELECT 1"}
