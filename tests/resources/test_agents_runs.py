"""Tests for client.agents.runs.list() and get()."""

import httpx
import pytest
import respx
from modus.types.agent_runs import AgentRun, AgentRunListItem

BASE = "https://api.modus.com"

SAMPLE_RUN = {
    "id": "wf_1:temporal-1",
    "workflowId": "wf_1",
    "temporalRunId": "temporal-1",
    "agentId": 7,
    "agentName": "Weekly Revenue Report",
    "agentType": "task",
    "status": "completed",
    "startedAt": "2026-01-01T00:00:00.000Z",
    "endedAt": "2026-01-01T01:00:00.000Z",
}


@respx.mock
def test_agents_runs_list(client):
    respx.get(f"{BASE}/api/v1/agents/7/runs").mock(
        return_value=httpx.Response(
            200,
            json={
                "runs": [SAMPLE_RUN],
                "nextPageToken": "page-2",
                "counts": {"completed": 1},
            },
        )
    )
    page = client.agents.runs.list(7, page_size=25)
    assert len(page) == 1
    item = page.items[0]
    assert isinstance(item, AgentRunListItem)
    assert item.id == "wf_1:temporal-1"
    assert item.status == "completed"
    assert page.next_page_token == "page-2"


@respx.mock
def test_agents_runs_list_passes_query_params(client):
    route = respx.get(f"{BASE}/api/v1/agents/7/runs").mock(
        return_value=httpx.Response(
            200,
            json={"runs": [], "nextPageToken": None, "counts": {}},
        )
    )
    client.agents.runs.list(7, page_size=10, status="completed", search="report")
    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert params["pageSize"] == "10"
    assert params["status"] == "completed"
    assert params["search"] == "report"


@respx.mock
def test_agents_runs_list_empty_next_page_token(client):
    respx.get(f"{BASE}/api/v1/agents/7/runs").mock(
        return_value=httpx.Response(
            200,
            json={"runs": [SAMPLE_RUN], "nextPageToken": "", "counts": {}},
        )
    )
    page = client.agents.runs.list(7)
    assert page.has_next_page() is False


@respx.mock
def test_agents_runs_list_invalid_page_size(client):
    with pytest.raises(ValueError, match="page_size must be a positive int"):
        client.agents.runs.list(7, page_size=0)


@respx.mock
def test_agents_runs_list_page_size_over_max(client):
    with pytest.raises(ValueError, match="page_size must be <= 100"):
        client.agents.runs.list(7, page_size=101)


@respx.mock
def test_agents_runs_get(client):
    respx.get(f"{BASE}/api/v1/agents/7/runs/wf_1%3Atemporal-1").mock(
        return_value=httpx.Response(200, json={**SAMPLE_RUN, "source": "history"})
    )
    run = client.agents.runs.get(7, "wf_1:temporal-1")
    assert isinstance(run, AgentRun)
    assert run.agent_id == 7
    assert run.source == "history"


def test_agents_resource_has_runs(client):
    assert hasattr(client.agents, "runs")
    assert hasattr(client.agents.runs, "list")
    assert hasattr(client.agents.runs, "get")
