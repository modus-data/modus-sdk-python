"""Tests for client.scopes.get_context()."""

import httpx
import respx
from modus.types.context_compose import SkillContextComposition

BASE = "https://api.modus.com"


@respx.mock
def test_skills_get_context(client):
    respx.post(f"{BASE}/api/v1/scopes/42/context").mock(
        return_value=httpx.Response(
            200,
            json={
                "context": "## Tables\n\ncustomers",
                "contextItems": [],
                "originalCount": 10,
                "selectedCount": 3,
                "sessionId": "sess-abc",
            },
        )
    )
    result = client.scopes.get_context(
        42, "What tables describe churn?", limit=25
    )
    assert isinstance(result, SkillContextComposition)
    assert result.original_count == 10
    assert result.selected_count == 3
    assert result.session_id == "sess-abc"
    assert result.context == "## Tables\n\ncustomers"


@respx.mock
def test_skills_get_context_omits_limit_when_none(client):
    route = respx.post(f"{BASE}/api/v1/scopes/42/context").mock(
        return_value=httpx.Response(
            200,
            json={
                "context": "",
                "contextItems": [],
                "originalCount": 0,
                "selectedCount": 0,
                "sessionId": "sess-x",
            },
        )
    )
    client.scopes.get_context(42, "query")
    import json

    body = json.loads(route.calls.last.request.content)
    assert "limit" not in body
