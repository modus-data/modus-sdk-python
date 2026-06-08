"""Tests for mgmt.skills.list() and mgmt.skills.get()."""

import httpx
import pytest
import respx
from modus import NotFoundError
from modus.management.types.skills import Skill

BASE = "https://api.modus.com"


@respx.mock
def test_skills_list_returns_page_of_skills(client, skill_list_row):
    respx.get(f"{BASE}/api/v1/skills").mock(
        return_value=httpx.Response(200, json={"skills": [skill_list_row], "nextPageToken": None})
    )
    page = client.skills.list()
    assert len(page) == 1
    skill = page.items[0]
    assert isinstance(skill, Skill)
    assert skill.id == 10
    assert skill.slug == "snowflake-analyst"
    assert skill.status == "active"


@respx.mock
def test_skills_list_row_has_none_instructions(client, skill_list_row):
    """List rows must have variation fields as None."""
    respx.get(f"{BASE}/api/v1/skills").mock(
        return_value=httpx.Response(200, json={"skills": [skill_list_row], "nextPageToken": None})
    )
    skill = client.skills.list().items[0]
    assert skill.instructions is None
    assert skill.model is None


@respx.mock
def test_skills_list_row_has_guardrails(client, skill_list_row):
    """guardrails must be surfaced from accessConfig on list rows."""
    respx.get(f"{BASE}/api/v1/skills").mock(
        return_value=httpx.Response(200, json={"skills": [skill_list_row], "nextPageToken": None})
    )
    skill = client.skills.list().items[0]
    assert skill.guardrails == ["no-pii"]


@respx.mock
def test_skills_get_populates_variation_fields(client, skill_detail_row):
    """get() must return Skill with instructions, model etc. populated."""
    respx.get(f"{BASE}/api/v1/skills/10").mock(
        return_value=httpx.Response(200, json=skill_detail_row)
    )
    skill = client.skills.get(10)
    assert skill.instructions == ["You are a Snowflake data analyst.", "Use SQL for queries."]
    assert skill.model == "gpt-4o"
    assert skill.expected_output == "Structured JSON with data rows"
    assert skill.toolset is not None
    assert skill.toolset.tools() == {
        "sql_runner": ["SELECT:conn-snowflake-001:analytics:public"],
        "memory": {"enabled": True},
    }
    assert skill.connection_set is not None
    assert skill.connection_set[0].model_dump(by_alias=True).get("connectionId") == "conn-snowflake-001"


@respx.mock
def test_skills_get_not_found(client):
    respx.get(f"{BASE}/api/v1/skills/999").mock(
        return_value=httpx.Response(404, json={"message": "Skill not found"})
    )
    with pytest.raises(NotFoundError, match="Skill not found"):
        client.skills.get(999)


@respx.mock
def test_skills_get_by_slug(client, skill_detail_row):
    respx.get(f"{BASE}/api/v1/skills/snowflake-analyst").mock(
        return_value=httpx.Response(200, json=skill_detail_row)
    )
    skill = client.skills.get("snowflake-analyst")
    assert skill.slug == "snowflake-analyst"
