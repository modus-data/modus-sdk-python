"""Tests for client.skills.get_context()."""

import httpx
import pytest
import respx
from modus.types.context_compose import SkillContextComposition

BASE = "https://api.modus.com"


@respx.mock
def test_skills_get_context(client):
    respx.post(f"{BASE}/api/v1/skills/42/context").mock(
        return_value=httpx.Response(
            200,
            json={
                "contextItems": [{"uid": "ctx-1", "title": "Churn table"}],
                "originalCount": 10,
                "sessionId": "sess-abc",
            },
        )
    )
    result = client.skills.get_context(
        42, "What tables describe churn?", limit=25
    )
    assert isinstance(result, SkillContextComposition)
    assert result.original_count == 10
    assert result.session_id == "sess-abc"
    assert len(result.context_items) == 1


@respx.mock
def test_skills_get_context_omits_limit_when_none(client):
    route = respx.post(f"{BASE}/api/v1/skills/42/context").mock(
        return_value=httpx.Response(
            200,
            json={
                "contextItems": [],
                "originalCount": 0,
                "sessionId": "sess-x",
            },
        )
    )
    client.skills.get_context(42, "query")
    import json

    body = json.loads(route.calls.last.request.content)
    assert "limit" not in body
