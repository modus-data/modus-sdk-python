"""Stream Accept negotiation + runs.create_modus sessionId mint."""

from __future__ import annotations

from uuid import UUID

import httpx
import respx
from modus._config import ModusConfig
from modus._http import HttpClient
from modus.resources.workflows.runs import _request_body

AGENT = "https://agent.example.com"


def test_request_body_mints_session_id_when_omitted():
    body = _request_body({"message": "hi"})
    assert "sessionId" in body
    UUID(body["sessionId"])


def test_request_body_keeps_explicit_session_id():
    body = _request_body({"message": "hi", "sessionId": "thread-abc"})
    assert body["sessionId"] == "thread-abc"


@respx.mock
def test_stream_post_sends_accept_event_stream():
    route = respx.post(f"{AGENT}/agent/v1/modus/runs").mock(
        return_value=httpx.Response(
            200,
            headers={"Content-Type": "text/event-stream"},
            text='data: {"type":"done","runId":"r1"}\n\n',
        )
    )
    http = HttpClient(ModusConfig(api_key="modus_test_key_stream", base_url=AGENT))
    list(http.stream_post("/agent/v1/modus/runs", json={"message": "hi"}))
    assert route.calls[0].request.headers.get("Accept") == "text/event-stream"
