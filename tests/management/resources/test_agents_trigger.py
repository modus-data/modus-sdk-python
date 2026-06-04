"""Tests for typed triggers on mgmt.agents."""

import json

import httpx
import respx
from modus.management import ModusManagement
from modus.management.types.agents import Agent
from modus.management.types.triggers import AgentTrigger

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
    "accessConfig": {"guardrails": [], "permissions": {}},
    "createdAt": "2026-01-01T00:00:00Z",
    "updatedAt": "2026-01-01T00:00:00Z",
    "deletedAt": None,
    "variation": {
        "trigger": {"triggerType": "manual"},
        "instructions": ["Do work"],
        "model": "gpt-4o",
    },
}


@respx.mock
def test_agents_create_serializes_typed_trigger() -> None:
    route = respx.post(f"{BASE}/api/v1/agents").mock(
        return_value=httpx.Response(201, json=AGENT_WITH_TRIGGER)
    )
    client = ModusManagement(api_key="modus_test_key", base_url=BASE)
    agent = client.agents.create(
        name="My Agent",
        type="task",
        trigger=AgentTrigger.manual(),
    )
    assert isinstance(agent, Agent)
    body = json.loads(route.calls[0].request.read())
    assert body["trigger"]["trigger_type"] == "manual"


@respx.mock
def test_agents_get_parses_trigger() -> None:
    respx.get(f"{BASE}/api/v1/agents/1").mock(
        return_value=httpx.Response(200, json=AGENT_WITH_TRIGGER)
    )
    client = ModusManagement(api_key="modus_test_key", base_url=BASE)
    agent = client.agents.get(1)
    assert agent.trigger is not None
    assert agent.trigger.trigger_type == "manual"
