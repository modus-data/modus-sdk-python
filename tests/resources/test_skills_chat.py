"""Tests for client.skills.chat() and chat_stream()."""

from __future__ import annotations

import json
from unittest.mock import patch

import httpx
import pytest
import respx
from modus import ModusError
from modus.types.runs import TokenEvent

BASE = "https://api.modus.com"
MODEL = "claude-sonnet-4.6"


@respx.mock
def test_skills_chat_new_thread(client):
    route = respx.post(f"{BASE}/api/v1/skills/42/chat").mock(
        return_value=httpx.Response(
            200,
            json={
                "content": "Hello back",
                "threadId": "thread-abc",
                "runId": "run-xyz",
            },
        )
    )
    result = client.skills.chat(42, "Hello", model=MODEL)
    assert route.called
    assert result.text == "Hello back"
    assert result.thread_id == "thread-abc"
    assert result.run_id == "run-xyz"
    request = route.calls.last.request
    body = json.loads(request.content)
    assert body == {"message": "Hello", "model": MODEL}


@respx.mock
def test_skills_chat_blank_thread_id_uses_new_chat_path(client):
    route = respx.post(f"{BASE}/api/v1/skills/42/chat").mock(
        return_value=httpx.Response(
            200,
            json={"content": "ok", "threadId": "t1", "runId": "r1"},
        )
    )
    client.skills.chat(42, "Hi", model=MODEL, thread_id="")
    assert route.called
    assert "/conversations/" not in str(route.calls.last.request.url)


@respx.mock
def test_skills_chat_continue(client):
    route = respx.post(
        f"{BASE}/api/v1/skills/42/conversations/thread-abc/chat"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "content": "Follow-up",
                "threadId": "thread-abc",
                "runId": "run-2",
            },
        )
    )
    result = client.skills.chat(
        42, "And then?", model=MODEL, thread_id="thread-abc"
    )
    assert route.called
    assert result.text == "Follow-up"


@respx.mock
def test_skills_chat_invalid_model(client):
    with pytest.raises(ValueError, match="model must be one of"):
        client.skills.chat(42, "Hi", model="not-a-real-model")


def test_skills_chat_stream(client):
    def fake_stream_post(path: str, *, json=None):
        assert path == "/api/v1/skills/42/chat/stream"
        assert json == {"message": "Stream me", "model": MODEL}
        yield 'data: {"type":"token","content":"Hi"}'
        yield 'data: {"type":"token","content":" there"}'
        yield (
            'data: {"type":"done","runId":"run-s1",'
            '"threadId":"thread-s1"}'
        )

    with patch.object(client._http, "stream_post", fake_stream_post):
        with client.skills.chat_stream(42, "Stream me", model=MODEL) as stream:
            chunks = list(stream.text_stream)
            final = stream.get_final_result()

    assert chunks == ["Hi", " there"]
    assert final.text == "Hi there"
    assert final.thread_id == "thread-s1"
    assert final.run_id == "run-s1"


def test_skills_chat_stream_event_stream_populates_final_text(client):
    def fake_stream_post(path: str, *, json=None):
        yield 'data: {"type":"token","content":"A"}'
        yield 'data: {"type":"done","runId":"r1","threadId":"t1"}'

    with patch.object(client._http, "stream_post", fake_stream_post):
        with client.skills.chat_stream(42, "x", model=MODEL) as stream:
            events = list(stream.event_stream)
            final = stream.get_final_result()

    assert len(events) == 2
    assert isinstance(events[0], TokenEvent)
    assert final.text == "A"


def test_skills_chat_stream_error_event(client):
    def fake_stream_post(path: str, *, json=None):
        yield 'data: {"type":"error","message":"Model unavailable"}'

    with patch.object(client._http, "stream_post", fake_stream_post):
        with client.skills.chat_stream(42, "x", model=MODEL) as stream:
            with pytest.raises(ModusError, match="Model unavailable"):
                list(stream.text_stream)


@respx.mock
def test_skills_chat_not_found(client):
    respx.post(f"{BASE}/api/v1/skills/999/chat").mock(
        return_value=httpx.Response(404, json={"message": "Skill not found"})
    )
    from modus import NotFoundError

    with pytest.raises(NotFoundError):
        client.skills.chat(999, "Hi", model=MODEL)
