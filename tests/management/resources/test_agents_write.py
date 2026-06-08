"""Tests for mgmt.agents.create/update/deploy/delete."""

import json

import httpx
import respx
from modus.management import ModusManagement
from modus.management.types.agents import Agent

BASE = "https://api.modus.com"

AGENT_RESP = {
    "id": 1, "slug": "my-agent", "name": "My Agent", "status": "draft",
    "type": "task", "description": None, "orgUuid": "org-xyz",
    "hasUnpublishedChanges": True, "isEnabled": False,
    "activeVariationId": None, "draftVariationId": "avar-new",
    "accessConfig": {"guardrails": [], "permissions": {}},
    "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z",
    "deletedAt": None,
}


def _client():
    return ModusManagement(api_key="modus_test_key", base_url=BASE)


@respx.mock
def test_agents_create():
    route = respx.post(f"{BASE}/api/v1/agents").mock(
        return_value=httpx.Response(201, json=AGENT_RESP)
    )
    agent = _client().agents.create(name="My Agent", type="task")
    assert isinstance(agent, Agent)
    body = json.loads(route.calls[0].request.read())
    assert body["name"] == "My Agent"
    assert body["type"] == "task"


@respx.mock
def test_agents_update():
    respx.patch(f"{BASE}/api/v1/agents/1").mock(
        return_value=httpx.Response(200, json=AGENT_RESP)
    )
    agent = _client().agents.update(1, name="Renamed Agent")
    assert isinstance(agent, Agent)


@respx.mock
def test_agents_update_type_and_mask():
    route = respx.patch(f"{BASE}/api/v1/agents/1").mock(
        return_value=httpx.Response(200, json=AGENT_RESP)
    )
    _client().agents.update(1, type="workflow", update_mask="type")
    req = route.calls[0].request
    assert req.url.params["updateMask"] == "type"
    body = json.loads(req.read())
    assert body["type"] == "workflow"


@respx.mock
def test_agents_update_without_mask_drops_unset_fields():
    route = respx.patch(f"{BASE}/api/v1/agents/1").mock(
        return_value=httpx.Response(200, json=AGENT_RESP)
    )
    _client().agents.update(1, name="Renamed Agent")
    body = json.loads(route.calls[0].request.read())
    # No mask → partial update: only the field we set is on the wire, no nulls.
    assert body == {"name": "Renamed Agent"}


@respx.mock
def test_agents_update_clears_field_via_mask():
    route = respx.patch(f"{BASE}/api/v1/agents/1").mock(
        return_value=httpx.Response(200, json=AGENT_RESP)
    )
    # Name the field in the mask and leave it unset → server clears it (null).
    _client().agents.update(1, update_mask="description")
    req = route.calls[0].request
    assert req.url.params["updateMask"] == "description"
    body = json.loads(req.read())
    assert "description" in body and body["description"] is None


@respx.mock
def test_agents_deploy():
    respx.post(f"{BASE}/api/v1/agents/1/deploy").mock(
        return_value=httpx.Response(200, json={"agent": {**AGENT_RESP, "status": "active"}})
    )
    agent = _client().agents.deploy(1)
    assert agent.status == "active"


@respx.mock
def test_agents_delete():
    respx.delete(f"{BASE}/api/v1/agents/1").mock(return_value=httpx.Response(204))
    result = _client().agents.delete(1)
    assert result is None
