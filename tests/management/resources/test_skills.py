"""Tests for mgmt.scopes.list() and mgmt.scopes.get()."""

import json

import httpx
import pytest
import respx
from modus import NotFoundError
from modus.management.types.skills import Skill

BASE = "https://api.modus.com"


@respx.mock
def test_skills_list_returns_page_of_skills(client, skill_list_row):
    respx.get(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(200, json={"scopes": [skill_list_row], "nextPageToken": None})
    )
    page = client.scopes.list()
    assert len(page) == 1
    skill = page.items[0]
    assert isinstance(skill, Skill)
    assert skill.id == 10
    assert skill.slug == "snowflake-analyst"
    assert skill.status == "active"


@respx.mock
def test_skills_list_row_has_none_instructions(client, skill_list_row):
    """List rows must have variation fields as None."""
    respx.get(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(200, json={"scopes": [skill_list_row], "nextPageToken": None})
    )
    skill = client.scopes.list().items[0]
    assert skill.variation is None


@respx.mock
def test_skills_list_row_has_guardrails(client, skill_list_row):
    """guardrails must be surfaced from accessConfig on list rows."""
    respx.get(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(200, json={"scopes": [skill_list_row], "nextPageToken": None})
    )
    skill = client.scopes.list().items[0]
    assert skill.access_config.guardrails == ["no-pii"]


@respx.mock
def test_skills_list_forwards_search_filter(client, skill_list_row):
    route = respx.get(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(200, json={"scopes": [skill_list_row], "nextPageToken": None})
    )
    client.scopes.list(search="churn")
    assert route.calls[0].request.url.params["search"] == "churn"


@respx.mock
def test_skills_list_omits_search_when_not_set(client, skill_list_row):
    route = respx.get(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(200, json={"scopes": [skill_list_row], "nextPageToken": None})
    )
    client.scopes.list()
    assert "search" not in route.calls[0].request.url.params


@respx.mock
def test_skills_get_populates_variation_fields(client, skill_detail_row):
    """get() must return Skill with instructions, model etc. populated."""
    respx.get(f"{BASE}/api/v1/scopes/10").mock(
        return_value=httpx.Response(200, json=skill_detail_row)
    )
    skill = client.scopes.get(10)
    assert skill.variation is not None
    assert skill.variation.instructions == [
        "You are a Snowflake data analyst.",
        "Use SQL for queries.",
    ]
    assert skill.variation.model == "gpt-4o"
    assert skill.variation.expected_output == "Structured JSON with data rows"
    assert skill.variation.toolset == {
        "sql_runner": ["SELECT:conn-snowflake-001:analytics:public"],
        "memory": {"enabled": True},
    }
    assert skill.variation.connection_set[0]["connectionId"] == "conn-snowflake-001"


@respx.mock
def test_skills_get_not_found(client):
    respx.get(f"{BASE}/api/v1/scopes/999").mock(
        return_value=httpx.Response(404, json={"message": "Skill not found"})
    )
    with pytest.raises(NotFoundError, match="Skill not found"):
        client.scopes.get(999)


@respx.mock
def test_skills_get_by_slug(client, skill_detail_row):
    respx.get(f"{BASE}/api/v1/scopes/snowflake-analyst").mock(
        return_value=httpx.Response(200, json=skill_detail_row)
    )
    skill = client.scopes.get("snowflake-analyst")
    assert skill.slug == "snowflake-analyst"


@respx.mock
def test_skills_request_ownership_transfer(client, skill_detail_row):
    route = respx.post(f"{BASE}/api/v1/scopes/10/transfer-ownership").mock(
        return_value=httpx.Response(200, json=skill_detail_row)
    )
    skill = client.scopes.request_ownership_transfer(10, new_owner_user_id="user_abc")
    assert skill.id == 10
    body = json.loads(route.calls[0].request.read())
    assert body["newOwnerUserId"] == "user_abc"


@respx.mock
def test_skills_cancel_ownership_transfer(client, skill_detail_row):
    respx.delete(f"{BASE}/api/v1/scopes/10/transfer-ownership").mock(
        return_value=httpx.Response(200, json=skill_detail_row)
    )
    skill = client.scopes.cancel_ownership_transfer(10)
    assert skill.slug == "snowflake-analyst"


@respx.mock
def test_skills_restore(client, skill_detail_row):
    respx.post(f"{BASE}/api/v1/scopes/10/restore").mock(
        return_value=httpx.Response(200, json=skill_detail_row)
    )
    skill = client.scopes.restore(10)
    assert skill.id == 10


@respx.mock
def test_skills_patch_mcp_config(client):
    route = respx.patch(f"{BASE}/api/v1/scopes/10/mcp-config").mock(
        return_value=httpx.Response(200, json={"config": {"coreTools": []}})
    )
    client.scopes.patch_mcp_config(10, mcp_config={"coreTools": {}})
    body = json.loads(route.calls[0].request.read())
    assert body["config"] == {"coreTools": {}}


@respx.mock
def test_skills_get_variation(client, skill_detail_row):
    uid = "00000000-0000-4000-a000-000000000abc"
    respx.get(f"{BASE}/api/v1/scopes/10/variations/{uid}").mock(
        return_value=httpx.Response(200, json=skill_detail_row)
    )
    skill = client.scopes.get_variation(10, variation_uid=uid)
    assert skill.variation is not None
    assert skill.variation.model == "gpt-4o"
