"""Tests for mgmt.scopes.create/update/deploy/delete."""

import json
from types import MappingProxyType

import httpx
import pytest
import respx
from modus.management import AsyncModusManagement, ModusManagement, Toolset
from modus.management.types.skills import Skill
from modus.types.json_blob import JsonObject
from modus.types.scopes import Scope

BASE = "https://api.modus.com"

SKILL_RESP = {
    "id": 1, "slug": "test-skill", "name": "Test Skill", "status": "draft",
    "description": None, "orgUuid": "org-xyz", "hasUnpublishedChanges": True,
    "activeVariationId": None, "draftVariationId": "var-new",
    "accessConfig": {"visibility": "shared", "groupPermissions": {"__everyone__": {"use": True, "manage": True}}, "guardrails": [], "sharedWith": []},
    "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z",
    "deletedAt": None,
    "canManage": True, "canUse": True, "manageDenial": None,
}

DEPLOY_RESP = {"scope": {**SKILL_RESP, "status": "active"}, "deployedAt": "2026-01-02T00:00:00Z"}


def _client():
    return ModusManagement(api_key="modus_test_key", base_url=BASE)


@respx.mock
def test_skills_create_minimal():
    route = respx.post(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(201, json=SKILL_RESP)
    )
    skill = _client().scopes.create(name="Test Skill")
    assert isinstance(skill, Skill)
    assert skill.name == "Test Skill"
    body = json.loads(route.calls[0].request.read())
    assert body["name"] == "Test Skill"


@respx.mock
def test_skills_create_sends_only_provided_fields():
    route = respx.post(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(201, json=SKILL_RESP)
    )
    _client().scopes.create(name="Test", description="Desc")
    body = json.loads(route.calls[0].request.read())
    assert set(body.keys()) == {"name", "description"}


@respx.mock
def test_skills_create_can_opt_out_of_own_learnings():
    route = respx.post(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(201, json=SKILL_RESP)
    )
    _client().scopes.create(name="Test", include_own_learnings=False)
    body = json.loads(route.calls[0].request.read())
    assert body == {"name": "Test", "includeOwnLearnings": False}


@respx.mock
def test_skills_create_can_opt_out_of_org_learnings():
    route = respx.post(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(201, json=SKILL_RESP)
    )
    _client().scopes.create(name="Test", include_org_learnings=False)
    body = json.loads(route.calls[0].request.read())
    assert body == {"name": "Test", "includeOrgLearnings": False}



@respx.mock
def test_skills_create_guardrails_sends_full_access_config():
    route = respx.post(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(201, json=SKILL_RESP)
    )
    _client().scopes.create(name="Test Skill", guardrails=["no-pii"])
    body = json.loads(route.calls[0].request.read())
    access = body["accessConfig"]
    assert access["guardrails"] == ["no-pii"]
    assert access["visibility"] == "shared"
    assert access["groupPermissions"]["__everyone__"] == {"use": True, "manage": True}
    assert "permissions" not in access


_PRIVATE_ACCESS_CONFIG = {
    "visibility": "private",
    "groupPermissions": {},
    "guardrails": [],
    "sharedWith": [{"email": "alice@example.com"}],
}


@respx.mock
def test_skills_update_guardrails_merges_existing_access_config():
    get_route = respx.get(f"{BASE}/api/v1/scopes/1").mock(
        return_value=httpx.Response(
            200,
            json={**SKILL_RESP, "accessConfig": _PRIVATE_ACCESS_CONFIG},
        )
    )
    patch_route = respx.patch(f"{BASE}/api/v1/scopes/1").mock(
        return_value=httpx.Response(200, json=SKILL_RESP)
    )
    _client().scopes.update(1, guardrails=["no-pii"])
    assert get_route.call_count == 1
    assert patch_route.call_count == 1
    body = json.loads(patch_route.calls[0].request.read())
    access = body["accessConfig"]
    assert access["guardrails"] == ["no-pii"]
    assert access["visibility"] == "private"
    assert access["sharedWith"] == [{"email": "alice@example.com"}]


@respx.mock
def test_skills_update_without_guardrails_skips_get():
    patch_route = respx.patch(f"{BASE}/api/v1/scopes/1").mock(
        return_value=httpx.Response(200, json=SKILL_RESP)
    )
    get_route = respx.get(f"{BASE}/api/v1/scopes/1")
    _client().scopes.update(1, name="Renamed")
    assert patch_route.called
    assert not get_route.called
    body = json.loads(patch_route.calls[0].request.read())
    assert body == {"name": "Renamed"}
    assert "accessConfig" not in body


@respx.mock
def test_skills_create_with_toolset_factory():
    from modus.management import Toolset

    route = respx.post(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(201, json=SKILL_RESP)
    )
    _client().scopes.create(
        name="X",
        toolset=Toolset.combine(
            Toolset.slack(
                connection_id="11111111-1111-4111-8111-111111111111",
                actions=["SendMessage"],
            ),
            Toolset.sql("postgresql", connection_id="22222222-2222-4222-8222-222222222222"),
            Toolset.memory(),
        ),
    )
    body = json.loads(route.calls[0].request.read())
    assert body["toolset"] == {
        "slack": {
            "byConnection": {
                "11111111-1111-4111-8111-111111111111": {"actions": ["SendMessage"]}
            }
        },
        "postgresql": {
            "byConnection": {
                "22222222-2222-4222-8222-222222222222": {"actions": ["query"]}
            }
        },
        "memory": {"enabled": True},
    }


@respx.mock
def test_skills_create_empty_toolset_is_sent_as_no_tools():
    from modus.management import Toolset

    route = respx.post(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(201, json=SKILL_RESP)
    )
    _client().scopes.create(name="X", toolset=Toolset.empty())
    body = json.loads(route.calls[0].request.read())
    assert body["toolset"] == {}


@respx.mock
def test_skills_update_empty_toolset_clears_tools():
    from modus.management import Toolset

    route = respx.patch(f"{BASE}/api/v1/scopes/1").mock(
        return_value=httpx.Response(200, json=SKILL_RESP)
    )
    _client().scopes.update(1, toolset=Toolset.empty())
    assert json.loads(route.calls[0].request.read()) == {"toolset": {}}


@respx.mock
def test_skills_update_manager_id_is_an_int():
    route = respx.patch(f"{BASE}/api/v1/scopes/1").mock(
        return_value=httpx.Response(200, json=SKILL_RESP)
    )
    _client().scopes.update(1, manager_id=7)
    assert json.loads(route.calls[0].request.read()) == {"managerId": 7}


@respx.mock
def test_skills_update_mask_detaches_manager():
    route = respx.patch(url__regex=rf"{BASE}/api/v1/scopes/1\?.*").mock(
        return_value=httpx.Response(200, json=SKILL_RESP)
    )
    _client().scopes.update(1, update_mask="managerId")
    assert json.loads(route.calls[0].request.read()) == {"managerId": None}


@respx.mock
def test_skills_create_raw_toolset_dict_rejected():
    respx.post(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(201, json=SKILL_RESP)
    )
    with pytest.raises(TypeError, match="Toolset"):
        _client().scopes.create(
            name="X",
            toolset={"memory": {"enabled": True}},
        )


@respx.mock
def test_skills_create_with_instructions():
    route = respx.post(f"{BASE}/api/v1/scopes").mock(
        return_value=httpx.Response(201, json=SKILL_RESP)
    )
    _client().scopes.create(name="X", instructions=["Do this."], model="gpt-4o")
    body = json.loads(route.calls[0].request.read())
    assert body["instructions"] == ["Do this."]
    assert body["model"] == "gpt-4o"


@respx.mock
def test_skills_update_resends_connection_set_from_get(client, skill_detail_row):
    respx.get(f"{BASE}/api/v1/scopes/10").mock(
        return_value=httpx.Response(200, json=skill_detail_row)
    )
    route = respx.patch(f"{BASE}/api/v1/scopes/10").mock(
        return_value=httpx.Response(200, json=skill_detail_row)
    )
    scope = client.scopes.get(10)
    assert scope.variation is not None
    rows = scope.variation.connection_set
    assert rows
    client.scopes.update(10, connection_set=rows)
    body = json.loads(route.calls[0].request.read())
    assert body["connectionSet"] == [{"connection_id": "22222222-2222-4222-8222-222222222222", "preferences": {"mode": "all", "include": [], "exclude": []}}]


@respx.mock
def test_skills_update_accepts_a_read_only_mapping_row():
    route = respx.patch(f"{BASE}/api/v1/scopes/10").mock(
        return_value=httpx.Response(200, json={**SKILL_RESP, "id": 10})
    )
    row = {"connection_id": "22222222-2222-4222-8222-222222222222", "preferences": {"mode": "all", "include": [], "exclude": []}}
    _client().scopes.update(10, connection_set=[MappingProxyType(row)])
    body = json.loads(route.calls[0].request.read())
    assert body["connectionSet"] == [row]


@respx.mock
def test_skills_update():
    respx.patch(f"{BASE}/api/v1/scopes/1").mock(
        return_value=httpx.Response(200, json=SKILL_RESP)
    )
    skill = _client().scopes.update(1, name="New Name")
    assert isinstance(skill, Skill)


@respx.mock
def test_skills_update_evaluations_supervision_and_mask():
    route = respx.patch(f"{BASE}/api/v1/scopes/1").mock(
        return_value=httpx.Response(200, json=SKILL_RESP)
    )
    _client().scopes.update(
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
def test_skills_apply_selection_ops_omits_catalog_and_false_validate_only():
    route = respx.post(f"{BASE}/api/v1/scopes/1/applySelectionOps").mock(
        return_value=httpx.Response(200, json=SKILL_RESP)
    )
    ops = [{
        "op": "setConnectionPreferences",
        "connectionId": "11111111-1111-4111-8111-111111111111",
        "preferences": {"schemaVersion": 2, "mode": "all", "include": [], "exclude": []},
    }]
    skill = _client().scopes.apply_selection_ops(1, ops)
    assert isinstance(skill, Skill)
    body = json.loads(route.calls[0].request.read())
    assert body == {"ops": ops}
    assert "catalog" not in body
    assert "validateOnly" not in body


@respx.mock
def test_skills_apply_selection_ops_preview_sends_validate_only():
    route = respx.post(f"{BASE}/api/v1/scopes/1/applySelectionOps").mock(
        return_value=httpx.Response(200, json=SKILL_RESP)
    )
    _client().scopes.apply_selection_ops(1, [{"op": "setConnectionPreferences"}], validate_only=True, toolset={})
    body = json.loads(route.calls[0].request.read())
    assert body["validateOnly"] is True
    assert body["toolset"] == {}
    assert "catalog" not in body


@respx.mock
def test_skills_deploy():
    respx.post(f"{BASE}/api/v1/scopes/1/deploy").mock(
        return_value=httpx.Response(200, json=DEPLOY_RESP)
    )
    skill = _client().scopes.deploy(1)
    assert isinstance(skill, Scope)
    assert isinstance(skill, Skill)
    assert skill.status == "active"


@respx.mock
def test_skills_delete_returns_none():
    respx.delete(f"{BASE}/api/v1/scopes/1").mock(return_value=httpx.Response(204))
    result = _client().scopes.delete(1)
    assert result is None


@respx.mock
def test_skills_update_url_encodes_slug():
    route = respx.patch(f"{BASE}/api/v1/scopes/my%20skill").mock(
        return_value=httpx.Response(200, json=SKILL_RESP)
    )
    _client().scopes.update("my skill", name="X")
    assert route.called


@pytest.mark.parametrize("method", ["create", "update"])
@respx.mock
async def test_async_scopes_send_connection_toolset(method):
    connection_id = "11111111-1111-4111-8111-111111111111"
    rules = {"allowedChannelIds": ["C123"]}
    toolset = Toolset.slack(connection_id=connection_id, actions=["SendMessage"], rules=rules)
    if method == "create":
        route = respx.post(f"{BASE}/api/v1/scopes").mock(
            return_value=httpx.Response(201, json=SKILL_RESP)
        )
    else:
        route = respx.patch(f"{BASE}/api/v1/scopes/1").mock(
            return_value=httpx.Response(200, json=SKILL_RESP)
        )
    async with AsyncModusManagement(api_key="modus_test_key", base_url=BASE) as client:
        if method == "create":
            await client.scopes.create(name="X", toolset=toolset)
        else:
            await client.scopes.update(1, toolset=toolset)
    assert json.loads(route.calls[0].request.read())["toolset"] == {
        "slack": {"byConnection": {connection_id: {"actions": ["SendMessage"], "rules": rules}}}
    }
