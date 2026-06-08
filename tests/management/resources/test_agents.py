"""Tests for mgmt.agents.list() and mgmt.agents.get()."""

import httpx
import pytest
import respx
from modus import NotFoundError
from modus.management.types.agents import Agent

BASE = "https://api.modus.com"


@respx.mock
def test_agents_list_row_has_none_variation_fields(client, agent_list_row):
    respx.get(f"{BASE}/api/v1/agents").mock(
        return_value=httpx.Response(200, json={"agents": [agent_list_row], "nextPageToken": None})
    )
    agent = client.agents.list().items[0]
    assert isinstance(agent, Agent)
    assert agent.instructions is None
    assert agent.model is None


@respx.mock
def test_agents_list_forwards_search_and_type(client, agent_list_row):
    route = respx.get(f"{BASE}/api/v1/agents").mock(
        return_value=httpx.Response(200, json={"agents": [agent_list_row], "nextPageToken": None})
    )
    client.agents.list(search="sales", type="workflow")
    params = route.calls[0].request.url.params
    assert params["search"] == "sales"
    assert params["type"] == "workflow"


@respx.mock
def test_agents_list_omits_filters_when_not_set(client, agent_list_row):
    route = respx.get(f"{BASE}/api/v1/agents").mock(
        return_value=httpx.Response(200, json={"agents": [agent_list_row], "nextPageToken": None})
    )
    client.agents.list()
    params = route.calls[0].request.url.params
    assert "search" not in params
    assert "type" not in params


@respx.mock
def test_agents_get_populates_variation(client, agent_detail_row):
    respx.get(f"{BASE}/api/v1/agents/5").mock(
        return_value=httpx.Response(200, json=agent_detail_row)
    )
    agent = client.agents.get(5)
    assert agent.instructions == ["Run the weekly revenue SQL and email results."]
    assert agent.model == "gpt-4o-mini"


@respx.mock
def test_agents_get_not_found(client):
    respx.get(f"{BASE}/api/v1/agents/999").mock(
        return_value=httpx.Response(404, json={"message": "Agent not found"})
    )
    with pytest.raises(NotFoundError):
        client.agents.get(999)
