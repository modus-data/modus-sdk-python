"""Tests for client.agents.list() and client.agents.get()."""

import httpx
import pytest
import respx
from modus import NotFoundError
from modus.types.agents import Agent

BASE = "https://api.modus.com"


@respx.mock
def test_agents_list(client, sample_agent):
    respx.get(f"{BASE}/api/v1/agents").mock(
        return_value=httpx.Response(200, json={"agents": [sample_agent], "nextPageToken": None})
    )
    page = client.agents.list()
    assert len(page) == 1
    agent = page.items[0]
    assert isinstance(agent, Agent)
    assert agent.id == 7
    assert agent.type == "task"


@respx.mock
def test_agents_list_no_next_page(client, sample_agent):
    respx.get(f"{BASE}/api/v1/agents").mock(
        return_value=httpx.Response(200, json={"agents": [sample_agent], "nextPageToken": None})
    )
    page = client.agents.list()
    assert page.has_next_page() is False


@respx.mock
def test_agents_get(client, sample_agent):
    respx.get(f"{BASE}/api/v1/agents/7").mock(
        return_value=httpx.Response(200, json=sample_agent)
    )
    agent = client.agents.get(7)
    assert agent.id == 7
    assert agent.name == "Weekly Revenue Report"
    assert agent.status == "active"


@respx.mock
def test_agents_get_not_found(client):
    respx.get(f"{BASE}/api/v1/agents/999").mock(
        return_value=httpx.Response(404, json={"message": "Agent not found"})
    )
    with pytest.raises(NotFoundError):
        client.agents.get(999)


@respx.mock
def test_agents_get_url_encodes_slug(client, sample_agent):
    """Slugs with special characters must be percent-encoded in the URL path."""
    route = respx.get(f"{BASE}/api/v1/agents/weekly%20report%2Fv2").mock(
        return_value=httpx.Response(200, json=sample_agent)
    )
    client.agents.get("weekly report/v2")
    assert route.called
