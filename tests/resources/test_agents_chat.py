"""Tests for client.agents.chat() and chat_stream()."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
import respx

BASE = "https://api.modus.com"
MODEL = "claude-sonnet-4.6"


@respx.mock
def test_agents_chat(client):
    respx.post(f"{BASE}/api/v1/agents/7/chat").mock(
        return_value=httpx.Response(
            200,
            json={
                "content": "Report started",
                "threadId": "agent-thread-1",
                "runId": "agent-run-1",
            },
        )
    )
    result = client.agents.chat(7, "Run report", model=MODEL)
    assert result.text == "Report started"
    assert result.thread_id == "agent-thread-1"


def test_agents_chat_stream(client):
    def fake_stream_post(path: str, *, json=None):
        assert path == "/api/v1/agents/7/chat/stream"
        yield 'data: {"type":"token","content":"OK"}'
        yield (
            'data: {"type":"done","runId":"r1","threadId":"t1"}'
        )

    with patch.object(client._http, "stream_post", fake_stream_post):
        with client.agents.chat_stream(7, "Go", model=MODEL) as stream:
            text = "".join(stream.text_stream)
            final = stream.get_final_result()

    assert text == "OK"
    assert final.run_id == "r1"
