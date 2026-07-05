"""Tests for client.suggestions."""
from __future__ import annotations

import json

import httpx
import respx
from modus import Modus, SuggestionEventSource, SuggestionEventType

SAMPLE_SUGGESTION = {
    "id": "predefined:q1",
    "skill_id": 42,
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
    page = client.suggestions.list(page_size=5, skill_ids=[7, 42])
    assert page.items[0].label == "Revenue"
    params = route.calls[0].request.url.params
    assert params["pageSize"] == "5"
    assert params["skill_ids"] == "7,42"


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
        "event_type": "clicked",
        "source": "home",
        "skill_id": 42,
        "thread_id": "thread-1",
        "metadata": {"placement": "home"},
    }
