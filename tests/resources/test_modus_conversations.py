"""Tests for client.modus.conversations.list() and .get() (org-level Modus conversations)."""

import httpx
import respx
from modus.types.conversations import ConversationListItem

BASE = "https://api.modus.com"


@respx.mock
def test_conversations_list_sends_source_filters(client):
    route = respx.get(f"{BASE}/api/v1/modus/conversations").mock(
        return_value=httpx.Response(200, json={"conversations": [], "nextPageToken": None})
    )
    # source is only valid with omitted kind or kind="all" (API 422 otherwise)
    client.modus.conversations.list(kind="all", source="dashboard_copilot", source_ref="dash-1")
    params = route.calls[0].request.url.params
    assert params["kind"] == "all"
    assert params["source"] == "dashboard_copilot"
    assert params["sourceRef"] == "dash-1"


@respx.mock
def test_conversations_list_preserves_source_filters_on_next_page(client):
    route = respx.get(f"{BASE}/api/v1/modus/conversations").mock(
        side_effect=[
            httpx.Response(
                200,
                json={"conversations": [], "nextPageToken": "tok_p2"},
            ),
            httpx.Response(
                200,
                json={"conversations": [], "nextPageToken": None},
            ),
        ]
    )
    page = client.modus.conversations.list(
        kind="all", source="dashboard_copilot", source_ref="dash-1"
    )
    assert page.has_next_page()
    page.get_next_page()
    assert len(route.calls) == 2
    for call in route.calls:
        params = call.request.url.params
        assert params["kind"] == "all"
        assert params["source"] == "dashboard_copilot"
        assert params["sourceRef"] == "dash-1"
    assert route.calls[1].request.url.params["pageToken"] == "tok_p2"


@respx.mock
def test_conversations_list_omits_filters_by_default(client):
    route = respx.get(f"{BASE}/api/v1/modus/conversations").mock(
        return_value=httpx.Response(200, json={"conversations": [], "nextPageToken": None})
    )
    client.modus.conversations.list()
    params = route.calls[0].request.url.params
    assert "kind" not in params
    assert "source" not in params
    assert "sourceRef" not in params


@respx.mock
def test_conversations_list_returns_items(client):
    respx.get(f"{BASE}/api/v1/modus/conversations").mock(
        return_value=httpx.Response(200, json={
            "conversations": [
                {
                    "threadId": "thread-0",
                    "scopeId": 0,
                    "firstMessage": "Hi",
                    "title": None,
                    "messageCount": 1,
                    "createdAt": "2026-01-01T00:00:00.000Z",
                    "updatedAt": "2026-01-01T00:00:00.000Z",
                    "userIds": ["user-abc"],
                }
            ],
            "nextPageToken": None,
        })
    )
    page = client.modus.conversations.list()
    assert len(page) == 1
    assert isinstance(page.items[0], ConversationListItem)
