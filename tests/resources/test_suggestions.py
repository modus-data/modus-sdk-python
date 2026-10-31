"""Tests for client.suggestions."""
from __future__ import annotations

import json

import httpx
import modus
import pytest
import respx
from modus import AsyncModus, Modus, SuggestionEventSource, SuggestionEventType

SAMPLE_SUGGESTION = {
    "id": "predefined:q1",
    "skillId": 42,
    "label": "Revenue",
    "prompt": "Show me revenue",
}


@respx.mock
def test_suggestions_list():
    route = respx.get("https://api.test/api/v1/suggestions/questions").mock(
        return_value=httpx.Response(
            200,
            json={"suggestions": [SAMPLE_SUGGESTION], "nextPageToken": None},
        ),
    )
    client = Modus(api_key="modus_test", base_url="https://api.test")
    page = client.suggestions.list(page_size=5, scope_ids=[7, 42])
    assert page.items[0].label == "Revenue"
    params = route.calls[0].request.url.params
    assert params["pageSize"] == "5"
    assert params["scopeIds"] == "7,42"


@respx.mock
def test_suggestions_list_rejects_empty_scope_ids_before_any_request():
    # ``scopeIds=`` is a 400 on the server; dropping the filter would silently broaden the result.
    route = respx.get("https://api.test/api/v1/suggestions/questions")
    client = Modus(api_key="modus_test", base_url="https://api.test")
    with pytest.raises(modus.ValidationError, match="scope_ids.*at least one"):
        client.suggestions.list(scope_ids=[])
    assert not route.called


@respx.mock
async def test_async_suggestions_list_rejects_empty_scope_ids_before_any_request():
    route = respx.get("https://api.test/api/v1/suggestions/questions")
    async with AsyncModus(api_key="modus_test", base_url="https://api.test") as client:
        with pytest.raises(modus.ValidationError, match="scope_ids.*at least one"):
            await client.suggestions.list(scope_ids=[])
    assert not route.called


@respx.mock
def test_suggestions_record_event():
    route = respx.post(
        "https://api.test/api/v1/suggestions/questions/predefined%3Aq1/events"
    ).mock(return_value=httpx.Response(204))
    client = Modus(api_key="modus_test", base_url="https://api.test")
    client.suggestions.record_event(
        "predefined:q1",
        event_type=SuggestionEventType.clicked,
        source=SuggestionEventSource.home,
        skill_id=42,
        thread_id="thread-1",
        metadata={"placement": "home"},
    )
    assert json.loads(route.calls[0].request.content) == {
        "eventType": "clicked",
        "source": "home",
        "skillId": 42,
        "threadId": "thread-1",
        "metadata": {"placement": "home"},
    }
