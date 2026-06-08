"""Tests for mgmt.skills.create/update/deploy/delete."""

import json

import httpx
import pytest
import respx
from modus.management import ModusManagement
from modus.management.types.skills import Skill
from modus.types.json_blob import JsonObject

BASE = "https://api.modus.com"

SKILL_RESP = {
    "id": 1, "slug": "test-skill", "name": "Test Skill", "status": "draft",
    "description": None, "orgUuid": "org-xyz", "hasUnpublishedChanges": True,
    "activeVariationId": None, "draftVariationId": "var-new",
    "accessConfig": {"guardrails": [], "permissions": {}},
    "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z",
    "deletedAt": None,
}

DEPLOY_RESP = {"skill": {**SKILL_RESP, "status": "active"}, "deployedAt": "2026-01-02T00:00:00Z"}


def _client():
    return ModusManagement(api_key="modus_test_key", base_url=BASE)


@respx.mock
def test_skills_create_minimal():
    route = respx.post(f"{BASE}/api/v1/skills").mock(
        return_value=httpx.Response(201, json=SKILL_RESP)
    )
    skill = _client().skills.create(name="Test Skill")
    assert isinstance(skill, Skill)
    assert skill.name == "Test Skill"
    body = json.loads(route.calls[0].request.read())
    assert body["name"] == "Test Skill"


@respx.mock
def test_skills_create_sends_only_provided_fields():
    route = respx.post(f"{BASE}/api/v1/skills").mock(
        return_value=httpx.Response(201, json=SKILL_RESP)
    )
    _client().skills.create(name="Test", description="Desc")
    body = json.loads(route.calls[0].request.read())
    assert set(body.keys()) == {"name", "description"}


@respx.mock
def test_skills_create_with_toolset_factory():
    from modus.management import Toolset

    route = respx.post(f"{BASE}/api/v1/skills").mock(
        return_value=httpx.Response(201, json=SKILL_RESP)
    )
    _client().skills.create(
        name="X",
        toolset=Toolset.combine(
            Toolset.slack(actions=["SendMessage"]),
            Toolset.sql_runner(["SELECT:conn-1:analytics:public"]),
            Toolset.memory(),
        ),
    )
    body = json.loads(route.calls[0].request.read())
    assert body["toolset"] == {
        "slack": {"actions": ["SendMessage"]},
        "sql_runner": ["SELECT:conn-1:analytics:public"],
        "memory": {"enabled": True},
    }


@respx.mock
def test_skills_create_empty_toolset_is_omitted():
    from modus.management import Toolset

    route = respx.post(f"{BASE}/api/v1/skills").mock(
        return_value=httpx.Response(201, json=SKILL_RESP)
    )
    _client().skills.create(name="X", toolset=Toolset.empty())
    body = json.loads(route.calls[0].request.read())
    assert "toolset" not in body


@respx.mock
def test_skills_create_raw_toolset_dict_warns():
    route = respx.post(f"{BASE}/api/v1/skills").mock(
        return_value=httpx.Response(201, json=SKILL_RESP)
    )
    with pytest.warns(DeprecationWarning, match="toolset"):
        _client().skills.create(
            name="X",
            toolset={"sql_runner": ["SELECT:conn-1:analytics:public"]},
        )
    body = json.loads(route.calls[0].request.read())
    assert body["toolset"] == {"sql_runner": ["SELECT:conn-1:analytics:public"]}
    assert route.called


@respx.mock
def test_skills_create_with_instructions():
    route = respx.post(f"{BASE}/api/v1/skills").mock(
        return_value=httpx.Response(201, json=SKILL_RESP)
    )
    _client().skills.create(name="X", instructions=["Do this."], model="gpt-4o")
    body = json.loads(route.calls[0].request.read())
    assert body["instructions"] == ["Do this."]
    assert body["model"] == "gpt-4o"


@respx.mock
def test_skills_update():
    respx.patch(f"{BASE}/api/v1/skills/1").mock(
        return_value=httpx.Response(200, json=SKILL_RESP)
    )
    skill = _client().skills.update(1, name="New Name")
    assert isinstance(skill, Skill)


@respx.mock
def test_skills_update_evaluations_supervision_and_mask():
    route = respx.patch(f"{BASE}/api/v1/skills/1").mock(
        return_value=httpx.Response(200, json=SKILL_RESP)
    )
    _client().skills.update(
        1,
        evaluations=[JsonObject.from_dict({"task": "t", "expectedOutput": "o"})],
        supervision_subordinate_descriptions={"12": "Reads facts"},
        update_mask="evaluations,supervisionSubordinateDescriptions",
    )
    req = route.calls[0].request
    assert req.url.params["updateMask"] == "evaluations,supervisionSubordinateDescriptions"
    body = json.loads(req.read())
    assert body["evaluations"] == [{"task": "t", "expectedOutput": "o"}]
    assert body["supervisionSubordinateDescriptions"] == {"12": "Reads facts"}


@respx.mock
def test_skills_deploy():
    respx.post(f"{BASE}/api/v1/skills/1/deploy").mock(
        return_value=httpx.Response(200, json=DEPLOY_RESP)
    )
    skill = _client().skills.deploy(1)
    assert isinstance(skill, Skill)
    assert skill.status == "active"


@respx.mock
def test_skills_delete_returns_none():
    respx.delete(f"{BASE}/api/v1/skills/1").mock(return_value=httpx.Response(204))
    result = _client().skills.delete(1)
    assert result is None


@respx.mock
def test_skills_update_url_encodes_slug():
    route = respx.patch(f"{BASE}/api/v1/skills/my%20skill").mock(
        return_value=httpx.Response(200, json=SKILL_RESP)
    )
    _client().skills.update("my skill", name="X")
    assert route.called
