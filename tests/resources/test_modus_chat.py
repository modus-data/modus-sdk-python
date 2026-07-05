"""Tests for client.modus chat paths."""
from __future__ import annotations

import pytest
import respx
from httpx import Response
from modus import Modus
from modus._chat import _modus_chat_path

BASE = "https://api.modus.com"


@pytest.fixture
def client() -> Modus:
    return Modus(api_key="modus_test", base_url=BASE)


def test_modus_chat_path_new_thread():
    assert _modus_chat_path(thread_id=None, stream=False) == "/api/v1/modus/chat"
    assert _modus_chat_path(thread_id=None, stream=True) == "/api/v1/modus/chat/stream"


def test_modus_chat_path_continue():
    tid = "agent_0_550e8400-e29b-41d4-a716-446655440000"
    assert (
        _modus_chat_path(thread_id=tid, stream=False)
        == f"/api/v1/modus/conversations/{tid}/chat"
    )


@respx.mock
def test_modus_chat_buffered(client: Modus):
    respx.post(f"{BASE}/api/v1/modus/chat").mock(
        return_value=Response(
            200,
            json={
                "content": "Hello from Modus",
                "threadId": "agent_0_abc",
                "runId": "run-1",
            },
        )
    )
    result = client.modus.chat("hi", model="claude-sonnet-5")
    assert result.content == "Hello from Modus"
    assert result.thread_id == "agent_0_abc"
