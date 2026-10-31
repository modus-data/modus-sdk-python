"""Tests for mgmt.workflows.create/update/deploy/delete."""

import inspect
import json

import httpx
import pytest
import respx
from modus.management import AgentSelection, ModusManagement
from modus.management.resources.workflows.workflows import (
    AsyncWorkflowsResource,
    WorkflowsResource,
)
from modus.management.types.agent_selection import parse_agent_selection
from modus.management.types.agents import Agent

BASE = "https://api.modus.com"

AGENT_RESP = {
    "id": 1, "slug": "my-agent", "name": "My Agent", "status": "draft",
    "type": "task", "description": None, "orgUuid": "org-xyz",
    "hasUnpublishedChanges": True, "isEnabled": False,
    "activeVariationId": None, "draftVariationId": "avar-new",
    "accessConfig": {"visibility": "shared", "groupPermissions": {"__everyone__": {"use": True, "manage": True}}, "guardrails": [], "sharedWith": []},
    "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z",
    "deletedAt": None,
    "canManage": True, "canUse": True, "manageDenial": None,
}


def _client():
    return ModusManagement(api_key="modus_test_key", base_url=BASE)


@respx.mock
def test_agents_create():
    route = respx.post(f"{BASE}/api/v1/workflows").mock(
        return_value=httpx.Response(201, json=AGENT_RESP)
    )
    agent = _client().workflows.create(name="My Agent", type="workflow")
    assert isinstance(agent, Agent)
    body = json.loads(route.calls[0].request.read())
    assert body == {"name": "My Agent", "type": "workflow"}


@respx.mock
def test_agents_create_agent_selection_snake_case():
    route = respx.post(f"{BASE}/api/v1/workflows").mock(
        return_value=httpx.Response(201, json=AGENT_RESP)
    )
    _client().workflows.create(
        name="My Agent",
        type="task",
        agent_selection=AgentSelection.single(17, model="gpt-4o"),
    )
    body = json.loads(route.calls[0].request.read())
    entry = body["agentSelection"]["agents"][0]
    assert "agent_id" in entry
    assert "priority_order" in entry
    assert "agentId" not in entry
    assert "priorityOrder" not in entry


@respx.mock
def test_agents_update_resends_model_settings_from_get():
    selection = {
        "agents": [{"agent_id": 17, "priority_order": 1}],
        "model": "gpt-4o",
        "modelSettings": {"reasoningEffort": "high", "contextWindow": 200000},
    }
    respx.get(f"{BASE}/api/v1/workflows/1").mock(
        return_value=httpx.Response(200, json={**AGENT_RESP, "variation": {"agentSelection": selection}})
    )
    route = respx.patch(f"{BASE}/api/v1/workflows/1").mock(
        return_value=httpx.Response(200, json=AGENT_RESP)
    )
    client = _client()
    fetched = client.workflows.get(1)
    assert fetched.variation is not None
    client.workflows.update(1, agent_selection=parse_agent_selection(fetched.variation.agent_selection))
    body = json.loads(route.calls[0].request.read())
    assert body["agentSelection"] == selection


@pytest.mark.parametrize("resource", [WorkflowsResource, AsyncWorkflowsResource])
@pytest.mark.parametrize("method", ["create", "update"])
def test_workflows_take_no_guardrails(resource, method):
    """The workflow access DTO has no ``guardrails``: every call that set it was a 400."""
    assert "guardrails" not in inspect.signature(getattr(resource, method)).parameters


@respx.mock
def test_agents_update():
    respx.patch(f"{BASE}/api/v1/workflows/1").mock(
        return_value=httpx.Response(200, json=AGENT_RESP)
    )
    agent = _client().workflows.update(1, name="Renamed Agent")
    assert isinstance(agent, Agent)


@respx.mock
def test_agents_update_type_and_mask():
    route = respx.patch(f"{BASE}/api/v1/workflows/1").mock(
        return_value=httpx.Response(200, json=AGENT_RESP)
    )
    _client().workflows.update(1, type="workflow", update_mask="type")
    req = route.calls[0].request
    assert req.url.params["updateMask"] == "type"
    body = json.loads(req.read())
    assert body["type"] == "workflow"


@respx.mock
def test_agents_update_without_mask_drops_unset_fields():
    route = respx.patch(f"{BASE}/api/v1/workflows/1").mock(
        return_value=httpx.Response(200, json=AGENT_RESP)
    )
    _client().workflows.update(1, name="Renamed Agent")
    body = json.loads(route.calls[0].request.read())
    # No mask → partial update: only the field we set is on the wire, no nulls.
    assert body == {"name": "Renamed Agent"}


@respx.mock
def test_agents_update_clears_field_via_mask():
    route = respx.patch(f"{BASE}/api/v1/workflows/1").mock(
        return_value=httpx.Response(200, json=AGENT_RESP)
    )
    # Name the field in the mask and leave it unset → server clears it (null).
    _client().workflows.update(1, update_mask="description")
    req = route.calls[0].request
    assert req.url.params["updateMask"] == "description"
    body = json.loads(req.read())
    assert "description" in body and body["description"] is None


@respx.mock
def test_agents_deploy():
    respx.post(f"{BASE}/api/v1/workflows/1/deploy").mock(
        return_value=httpx.Response(
            200,
            json={
                "workflow": {**AGENT_RESP, "status": "active"},
                "deployedAt": "2026-01-02T00:00:00Z",
            },
        )
    )
    agent = _client().workflows.deploy(1)
    assert isinstance(agent, Agent)
    assert agent.status == "active"


@respx.mock
def test_agents_delete():
    respx.delete(f"{BASE}/api/v1/workflows/1").mock(return_value=httpx.Response(204))
    result = _client().workflows.delete(1)
    assert result is None
