"""Tests for typed triggers on mgmt.workflows."""

import json

import httpx
import respx
from modus.management import ModusManagement
from modus.management.types.agents import Agent
from modus.management.types.triggers import AgentTrigger, parse_trigger

BASE = "https://api.modus.com"

AGENT_WITH_TRIGGER = {
    "id": 1,
    "slug": "my-agent",
    "name": "My Agent",
    "status": "draft",
    "type": "task",
    "description": None,
    "orgUuid": "org-xyz",
    "hasUnpublishedChanges": True,
    "isEnabled": False,
    "activeVariationId": None,
    "draftVariationId": "avar-new",
    "accessConfig": {"visibility": "shared", "groupPermissions": {"__everyone__": {"use": True, "manage": True}}, "guardrails": [], "sharedWith": []},
    "createdAt": "2026-01-01T00:00:00Z",
    "updatedAt": "2026-01-01T00:00:00Z",
    "deletedAt": None,
    "canManage": True,
    "canUse": True,
    "manageDenial": None,
    "variation": {
        "trigger": {"triggerType": "manual"},
        "agentSelection": {"agents": [], "model": "gpt-4o"},
    },
}


@respx.mock
def test_agents_create_serializes_typed_trigger() -> None:
    route = respx.post(f"{BASE}/api/v1/workflows").mock(
        return_value=httpx.Response(201, json=AGENT_WITH_TRIGGER)
    )
    client = ModusManagement(api_key="modus_test_key", base_url=BASE)
    agent = client.workflows.create(
        name="My Agent",
        type="task",
        trigger=AgentTrigger.manual(),
    )
    assert isinstance(agent, Agent)
    body = json.loads(route.calls[0].request.read())
    assert body["trigger"]["trigger_type"] == "manual"


@respx.mock
def test_agents_get_parses_trigger() -> None:
    respx.get(f"{BASE}/api/v1/workflows/1").mock(
        return_value=httpx.Response(200, json=AGENT_WITH_TRIGGER)
    )
    client = ModusManagement(api_key="modus_test_key", base_url=BASE)
    agent = client.workflows.get(1)
    assert agent.variation is not None
    trigger = parse_trigger(agent.variation.trigger)
    assert trigger is not None
    assert trigger.trigger_type == "manual"
