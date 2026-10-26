"""Tests for client.workflows.runs.list() and get()."""

import json

import httpx
import pytest
import respx
from modus import Modus
from modus.types.agent_runs import (
    ActiveConversationRun,
    AgentRun,
    AgentRunListItem,
    RunAdmission,
)
from modus.types.runs import DoneEvent

BASE = "https://api.modus.com"
AGENT_BASE = "https://agent.modus.com"

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
    respx.get(f"{BASE}/api/v1/workflows/7/runs").mock(
        return_value=httpx.Response(
            200,
            json={
                "runs": [SAMPLE_RUN],
                "nextPageToken": "page-2",
                "counts": {"completed": 1},
            },
        )
    )
    page = client.workflows.runs.list(7, page_size=25)
    assert len(page) == 1
    item = page.items[0]
    assert isinstance(item, AgentRunListItem)
    assert item.id == "wf_1:temporal-1"
    assert item.status == "completed"
    assert page.next_page_token == "page-2"


@respx.mock
def test_agents_runs_list_passes_query_params(client):
    route = respx.get(f"{BASE}/api/v1/workflows/7/runs").mock(
        return_value=httpx.Response(
            200,
            json={"runs": [], "nextPageToken": None, "counts": {}},
        )
    )
    client.workflows.runs.list(7, page_size=10, status="completed", search="report")
    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert params["pageSize"] == "10"
    assert params["status"] == "completed"
    assert params["search"] == "report"


@respx.mock
def test_agents_runs_list_empty_next_page_token(client):
    respx.get(f"{BASE}/api/v1/workflows/7/runs").mock(
        return_value=httpx.Response(
            200,
            json={"runs": [SAMPLE_RUN], "nextPageToken": "", "counts": {}},
        )
    )
    page = client.workflows.runs.list(7)
    assert page.has_next_page() is False


@respx.mock
def test_agents_runs_list_invalid_page_size(client):
    with pytest.raises(ValueError, match="page_size must be a positive int"):
        client.workflows.runs.list(7, page_size=0)


@respx.mock
def test_agents_runs_list_page_size_over_max(client):
    with pytest.raises(ValueError, match="page_size must be <= 100"):
        client.workflows.runs.list(7, page_size=101)


@respx.mock
def test_agents_runs_get(client):
    respx.get(f"{BASE}/api/v1/workflows/7/runs/wf_1%3Atemporal-1").mock(
        return_value=httpx.Response(200, json={**SAMPLE_RUN, "source": "history"})
    )
    run = client.workflows.runs.get(7, "wf_1:temporal-1")
    assert isinstance(run, AgentRun)
    assert run.agent_id == 7
    assert run.source == "history"


def test_agents_resource_has_runs(client):
    assert hasattr(client.workflows, "runs")
    assert hasattr(client.workflows.runs, "list")
    assert hasattr(client.workflows.runs, "active")
    assert hasattr(client.workflows.runs, "active_by_session")
    assert hasattr(client.workflows.runs, "get")
    assert hasattr(client.workflows.runs, "create")
    assert hasattr(client.workflows.runs, "cancel")


@respx.mock
def test_agents_runs_create_routes_to_agent_service():
    client = Modus(api_key="modus_test_key_abc123", base_url=BASE, agent_host=AGENT_BASE)
    route = respx.post(f"{AGENT_BASE}/agent/v1/workflows/7/runs").mock(
        return_value=httpx.Response(
            200,
            text='data: {"type":"done","runId":"run-1","threadId":"thread-1"}\n\n',
            headers={"content-type": "text/event-stream"},
        )
    )

    events = list(client.workflows.runs.create(7, {"message": "hello", "sessionId": "thread-1"}))

    assert route.called
    assert isinstance(events[0], DoneEvent)
    assert events[0].run_id == "run-1"


@respx.mock
def test_agents_runs_active_uses_agent_service():
    client = Modus(api_key="modus_test_key_abc123", base_url=BASE, agent_host=AGENT_BASE)
    route = respx.get(f"{AGENT_BASE}/agent/v1/runs/active").mock(
        return_value=httpx.Response(
            200,
            json={
                "runs": [
                    {
                        "runId": "run-active",
                        "sessionId": "thread-active",
                        "status": "running",
                        "message": "continue",
                        "createdAt": "2026-01-01T00:00:00.000Z",
                        "updatedAt": "2026-01-01T00:00:01.000Z",
                    }
                ],
                "nextPageToken": "page-2",
            },
        )
    )

    page = client.workflows.runs.active(page_size=10, page_token="tok_abc")

    assert route.called
    assert dict(route.calls.last.request.url.params) == {
        "pageSize": "10",
        "pageToken": "tok_abc",
    }
    assert isinstance(page.items[0], ActiveConversationRun)
    assert page.items[0].run_id == "run-active"
    assert page.next_page_token == "page-2"


@respx.mock
def test_agents_runs_active_by_session_uses_agent_service():
    client = Modus(api_key="modus_test_key_abc123", base_url=BASE, agent_host=AGENT_BASE)
    route = respx.post(f"{AGENT_BASE}/agent/v1/runs/active-by-session").mock(
        return_value=httpx.Response(200, json={"runs": []})
    )

    runs = client.workflows.runs.active_by_session(
        ["thread-active", " thread-active ", ""]
    )

    assert route.called
    assert json.loads(route.calls.last.request.content.decode()) == {
        "sessionIds": ["thread-active"]
    }
    assert runs == []


@respx.mock
def test_agents_runs_cancel_uses_agent_service():
    client = Modus(api_key="modus_test_key_abc123", base_url=BASE, agent_host=AGENT_BASE)
    route = respx.post(f"{AGENT_BASE}/agent/v1/runs/run-1/cancel").mock(
        return_value=httpx.Response(204)
    )

    client.workflows.runs.cancel("run-1")

    assert route.called


def _agent_client(max_retries: int = 0) -> Modus:
    return Modus(
        api_key="modus_test_key_abc123",
        base_url=BASE,
        agent_host=AGENT_BASE,
        max_retries=max_retries,
    )


@respx.mock
def test_runs_interrupt_sends_the_follow_up_turn_and_returns_the_new_run():
    route = respx.post(f"{AGENT_BASE}/agent/v1/runs/run-1/interrupt").mock(
        return_value=httpx.Response(202, json={"runId": "run-steer", "status": "pending"})
    )

    admitted = _agent_client().workflows.runs.interrupt(
        "run-1",
        {"message": "Only count EMEA.", "sessionId": "thread-1"},
        last_seen_event_id="1717000000000-0",
    )

    assert isinstance(admitted, RunAdmission)
    assert (admitted.run_id, admitted.status) == ("run-steer", "pending")
    sent = json.loads(route.calls.last.request.content)
    assert sent["lastSeenEventId"] == "1717000000000-0"
    assert sent["nextRun"]["message"] == "Only count EMEA."
    assert sent["nextRun"]["sessionId"] == "thread-1"
    assert sent["nextRun"]["runId"]


@respx.mock
def test_runs_interrupt_retry_reuses_the_pinned_run_id():
    route = respx.post(f"{AGENT_BASE}/agent/v1/runs/run-1/interrupt").mock(
        side_effect=[
            httpx.Response(500, json={"error": {"code": "INTERNAL_ERROR", "message": "boom"}}),
            httpx.Response(202, json={"runId": "run-steer", "status": "pending"}),
        ]
    )

    _agent_client(max_retries=1).workflows.runs.interrupt(
        "run-1", {"message": "m", "sessionId": "thread-1"}
    )

    assert route.call_count == 2
    first, second = (json.loads(call.request.content) for call in route.calls)
    assert second["nextRun"]["runId"] == first["nextRun"]["runId"]


@respx.mock
def test_runs_edit_queued_sends_the_replacement_turn_and_returns_the_run():
    route = respx.post(f"{AGENT_BASE}/agent/v1/runs/run-q/queue-edit").mock(
        return_value=httpx.Response(200, json={"runId": "run-q", "status": "queued"})
    )

    edited = _agent_client().workflows.runs.edit_queued(
        "run-q", {"message": "edited", "sessionId": "thread-1"}
    )

    assert (edited.run_id, edited.status) == ("run-q", "queued")
    assert json.loads(route.calls.last.request.content) == {
        "nextRun": {"message": "edited", "sessionId": "thread-1"}
    }


@respx.mock
async def test_async_runs_interrupt_pins_the_run_id_and_returns_the_new_run():
    from modus import AsyncModus

    route = respx.post(f"{AGENT_BASE}/agent/v1/runs/run-1/interrupt").mock(
        return_value=httpx.Response(202, json={"runId": "run-steer", "status": "pending"})
    )
    client = AsyncModus(api_key="modus_test_key_abc123", base_url=BASE, agent_host=AGENT_BASE)

    admitted = await client.workflows.runs.interrupt(
        "run-1", {"message": "m", "sessionId": "thread-1"}
    )

    assert admitted.run_id == "run-steer"
    assert json.loads(route.calls.last.request.content)["nextRun"]["runId"]
    with pytest.raises(ValueError, match="sessionId"):
        await client.workflows.runs.edit_queued("run-1", {"message": "m"})


@pytest.mark.parametrize(
    "call",
    [
        lambda runs: runs.interrupt("run-1", {"message": "m", "sessionId": " "}),
        lambda runs: runs.edit_queued("run-1", {"message": "m"}),
        lambda runs: list(runs.resume("run-1", {"decision": "approve"})),
    ],
    ids=["interrupt", "edit_queued", "resume"],
)
@respx.mock
def test_runs_continuations_refuse_a_missing_session_id_before_any_request(call):
    # No route is mocked, so a request would raise respx's error instead of ValueError.
    with pytest.raises(ValueError, match="sessionId"):
        call(_agent_client().workflows.runs)


@respx.mock
def test_runs_resume_sends_the_decision_without_a_message():
    route = respx.post(f"{AGENT_BASE}/agent/v1/runs/run-1/resume").mock(
        return_value=httpx.Response(
            200,
            text='data: {"type":"done","runId":"run-c","threadId":"thread-1"}\n\n',
            headers={"content-type": "text/event-stream"},
        )
    )

    list(
        _agent_client().workflows.runs.resume(
            "run-1", {"decision": "approve", "sessionId": "thread-1"}
        )
    )

    sent = json.loads(route.calls.last.request.content)
    assert sent["sessionId"] == "thread-1"
    assert "message" not in sent


@respx.mock
def test_agents_workflow_actions_execute_routes_to_agent_service():
    client = Modus(api_key="modus_test_key_abc123", base_url=BASE, agent_host=AGENT_BASE)
    route = respx.post(f"{AGENT_BASE}/agent/v1/workflow-actions").mock(
        return_value=httpx.Response(
            200,
            text='data: {"type":"done","runId":"wf-action-1","threadId":"thread-1"}\n\n',
            headers={"content-type": "text/event-stream"},
        )
    )

    events = list(
        client.workflows.workflow_actions.execute(
            {
                "organizationId": "org_123",
                "sessionId": "thread-1",
                "workflowAction": {"type": "noop"},
            }
        )
    )

    assert route.called
    assert isinstance(events[0], DoneEvent)
    assert events[0].run_id == "wf-action-1"
