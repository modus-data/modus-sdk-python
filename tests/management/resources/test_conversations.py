"""Tests for mgmt.scopes.conversations(skill_id).list() and .get()."""

import httpx
import respx
from modus.management.types.conversations import Conversation, ConversationListItem

BASE = "https://api.modus.com"


def _list_item(i: int = 0) -> dict:
    return {
        "threadId": f"thread-{i}",
        "skillId": 42,
        "firstMessage": f"Hello from thread {i}",
        "title": None,
        "messageCount": 3,
        "createdAt": "2026-01-01T00:00:00.000Z",
        "updatedAt": "2026-01-01T00:00:00.000Z",
        "userIds": ["user-abc"],
    }


@respx.mock
def test_conversations_list_is_scoped_to_skill(client):
    route = respx.get(f"{BASE}/api/v1/scopes/42/conversations").mock(
        return_value=httpx.Response(200, json={"conversations": [_list_item()], "nextPageToken": None})
    )
    page = client.scopes.conversations(42).list(page_size=10)
    assert len(page) == 1
    assert isinstance(page.items[0], ConversationListItem)
    assert route.calls[0].request.url.params["pageSize"] == "10"


@respx.mock
def test_conversations_get_is_scoped_to_skill(client):
    respx.get(f"{BASE}/api/v1/scopes/42/conversations/thread-abc").mock(
        return_value=httpx.Response(200, json={
            "threadId": "thread-abc",
            "skillId": 42,
            "messages": [{"type": "human", "content": "Hi"}],
            "createdAt": "2026-01-01T00:00:00.000Z",
            "updatedAt": "2026-01-01T00:00:00.000Z",
        })
    )
    conv = client.scopes.conversations(42).get("thread-abc")
    assert isinstance(conv, Conversation)
    assert conv.thread_id == "thread-abc"


@respx.mock
def test_conversations_list_url_encodes_skill_slug(client):
    route = respx.get(f"{BASE}/api/v1/scopes/my%20skill/conversations").mock(
        return_value=httpx.Response(200, json={"conversations": [], "nextPageToken": None})
    )
    client.scopes.conversations("my skill").list()
    assert route.called
