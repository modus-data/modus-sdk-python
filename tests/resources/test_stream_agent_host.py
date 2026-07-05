"""Tests: streaming chat methods must POST to agent-host runs paths.

Buffered chat (client.scopes.chat, client.modus.chat) stays on modus-api unchanged.
Streaming (client.scopes.chat_stream, client.modus.chat_stream,
           client.workflows.runs.chat_stream) POSTs to:

  skills  → {agent_host}/agent/v1/scopes/{id}/runs
  modus   → {agent_host}/agent/v1/modus/runs
  agents  → {agent_host}/agent/v1/workflows/{id}/runs

Body format:
  { "message": "...", "sessionId": "...", "config": { "model": "..." } }
  (sessionId omitted when thread_id is None)
  (version omitted unless explicitly passed)
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from modus import Modus

API_BASE = "https://api.modus.com"
AGENT_HOST = "https://agent.modus.com"
MODEL = "claude-sonnet-5"


@pytest.fixture
def client_with_agent_host() -> Modus:
    return Modus(api_key="modus_test_key_abc123", base_url=API_BASE, agent_host=AGENT_HOST)


@pytest.fixture
def client_no_agent_host() -> Modus:
    """When no agent_host is set, stream should fall back to base_url."""
    return Modus(api_key="modus_test_key_abc123", base_url=API_BASE)


# ---------------------------------------------------------------------------
# Skills stream → agent host
# ---------------------------------------------------------------------------


def test_skills_chat_stream_posts_to_agent_host(client_with_agent_host):
    """skills.chat_stream() must POST to agent-host /agent/v1/scopes/{id}/runs."""
    captured = {}

    def fake_stream_post(path: str, *, json=None):
        captured["path"] = path
        captured["json"] = json
        yield 'data: {"type":"token","content":"Hi"}'
        yield 'data: {"type":"done","runId":"r1","threadId":"t1"}'

    with patch.object(client_with_agent_host._agent_http, "stream_post", fake_stream_post):
        with client_with_agent_host.scopes.chat_stream(42, "Hello", model=MODEL) as stream:
            list(stream.text_stream)

    assert captured["path"] == "/agent/v1/scopes/42/runs"
    assert captured["json"]["message"] == "Hello"
    assert captured["json"]["config"] == {"model": MODEL}
    assert "sessionId" not in captured["json"]


def test_skills_chat_stream_includes_session_id_when_thread_id_given(client_with_agent_host):
    """skills.chat_stream(thread_id=...) must include sessionId in body."""
    captured = {}

    def fake_stream_post(path: str, *, json=None):
        captured["json"] = json
        yield 'data: {"type":"done","runId":"r1","threadId":"thread-abc"}'

    with patch.object(client_with_agent_host._agent_http, "stream_post", fake_stream_post):
        with client_with_agent_host.scopes.chat_stream(
            42, "Hi", model=MODEL, thread_id="thread-abc"
        ) as stream:
            list(stream.text_stream)

    assert captured["json"]["sessionId"] == "thread-abc"
    assert captured["json"]["message"] == "Hi"


def test_skills_chat_stream_blank_thread_id_omits_session_id(client_with_agent_host):
    """Blank thread_id must not send sessionId."""
    captured = {}

    def fake_stream_post(path: str, *, json=None):
        captured["json"] = json
        yield 'data: {"type":"done","runId":"r1","threadId":"t-new"}'

    with patch.object(client_with_agent_host._agent_http, "stream_post", fake_stream_post):
        with client_with_agent_host.scopes.chat_stream(
            42, "Hi", model=MODEL, thread_id="  "
        ) as stream:
            list(stream.text_stream)

    assert "sessionId" not in captured["json"]


def test_skills_chat_stream_with_version(client_with_agent_host):
    """skills.chat_stream(version='draft') must include version in body."""
    captured = {}

    def fake_stream_post(path: str, *, json=None):
        captured["json"] = json
        yield 'data: {"type":"done","runId":"r1","threadId":"t1"}'

    with patch.object(client_with_agent_host._agent_http, "stream_post", fake_stream_post):
        with client_with_agent_host.scopes.chat_stream(
            42, "Hi", model=MODEL, version="draft"
        ) as stream:
            list(stream.text_stream)

    assert captured["json"]["version"] == "draft"


def test_skills_chat_stream_url_encodes_slug(client_with_agent_host):
    """Skill slug with special chars is URL-encoded in the path."""
    captured = {}

    def fake_stream_post(path: str, *, json=None):
        captured["path"] = path
        yield 'data: {"type":"done","runId":"r1","threadId":"t1"}'

    with patch.object(client_with_agent_host._agent_http, "stream_post", fake_stream_post):
        with client_with_agent_host.scopes.chat_stream(
            "my skill/v2", "Hi", model=MODEL
        ) as stream:
            list(stream.text_stream)

    assert captured["path"] == "/agent/v1/scopes/my%20skill%2Fv2/runs"


# ---------------------------------------------------------------------------
# Buffered skills chat → still hits modus-api (unchanged)
# ---------------------------------------------------------------------------


def test_skills_chat_buffered_still_uses_api_host(client_with_agent_host):
    """Buffered chat must NOT use agent host — still hits modus-api path."""
    import json

    import httpx
    import respx

    with respx.mock:
        route = respx.post(f"{API_BASE}/api/v1/scopes/42/chat").mock(
            return_value=httpx.Response(
                200,
                json={"content": "ok", "threadId": "t1", "runId": "r1"},
            )
        )
        result = client_with_agent_host.scopes.chat(42, "Hello", model=MODEL)
        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body == {"message": "Hello", "model": MODEL}
        assert result.content == "ok"


# ---------------------------------------------------------------------------
# Modus stream → agent host
# ---------------------------------------------------------------------------


def test_modus_chat_stream_posts_to_agent_host(client_with_agent_host):
    """modus.chat_stream() must POST to agent-host /agent/v1/modus/runs."""
    captured = {}

    def fake_stream_post(path: str, *, json=None):
        captured["path"] = path
        captured["json"] = json
        yield 'data: {"type":"token","content":"Answer"}'
        yield 'data: {"type":"done","runId":"r2","threadId":"t2"}'

    with patch.object(client_with_agent_host._agent_http, "stream_post", fake_stream_post):
        with client_with_agent_host.modus.chat_stream("Tell me", model=MODEL) as stream:
            list(stream.text_stream)

    assert captured["path"] == "/agent/v1/modus/runs"
    assert captured["json"]["message"] == "Tell me"
    assert captured["json"]["config"] == {"model": MODEL}
    assert "sessionId" not in captured["json"]


def test_modus_chat_stream_includes_session_id(client_with_agent_host):
    """modus.chat_stream(thread_id=...) must include sessionId."""
    captured = {}

    def fake_stream_post(path: str, *, json=None):
        captured["json"] = json
        yield 'data: {"type":"done","runId":"r1","threadId":"thread-m1"}'

    with patch.object(client_with_agent_host._agent_http, "stream_post", fake_stream_post):
        with client_with_agent_host.modus.chat_stream(
            "Hi", model=MODEL, thread_id="thread-m1"
        ) as stream:
            list(stream.text_stream)

    assert captured["json"]["sessionId"] == "thread-m1"


def test_modus_chat_buffered_still_uses_api_host(client_with_agent_host):
    """Buffered modus chat must stay on modus-api path."""
    import httpx
    import respx

    with respx.mock:
        route = respx.post(f"{API_BASE}/api/v1/modus/chat").mock(
            return_value=httpx.Response(
                200,
                json={"content": "from modus", "threadId": "t1", "runId": "r1"},
            )
        )
        result = client_with_agent_host.modus.chat("Hello", model=MODEL)
        assert route.called
        assert result.content == "from modus"


# ---------------------------------------------------------------------------
# Agents stream → agent host
# ---------------------------------------------------------------------------


def test_agents_chat_stream_posts_to_agent_host(client_with_agent_host):
    """agents.chat_stream() must POST to agent-host /agent/v1/workflows/{id}/runs."""
    captured = {}

    def fake_stream_post(path: str, *, json=None):
        captured["path"] = path
        captured["json"] = json
        yield 'data: {"type":"done","runId":"r3","threadId":"t3"}'

    with patch.object(client_with_agent_host._agent_http, "stream_post", fake_stream_post):
        with client_with_agent_host.workflows.chat_stream(
            99, "Kick off", model=MODEL
        ) as stream:
            list(stream.text_stream)

    assert captured["path"] == "/agent/v1/workflows/99/runs"
    assert captured["json"]["message"] == "Kick off"
    assert captured["json"]["config"] == {"model": MODEL}


def test_agents_chat_stream_with_thread_id(client_with_agent_host):
    """agents.chat_stream(thread_id=...) includes sessionId."""
    captured = {}

    def fake_stream_post(path: str, *, json=None):
        captured["json"] = json
        yield 'data: {"type":"done","runId":"r1","threadId":"t-agent"}'

    with patch.object(client_with_agent_host._agent_http, "stream_post", fake_stream_post):
        with client_with_agent_host.workflows.chat_stream(
            99, "Hi", model=MODEL, thread_id="t-agent"
        ) as stream:
            list(stream.text_stream)

    assert captured["json"]["sessionId"] == "t-agent"


# ---------------------------------------------------------------------------
# No agent_host fallback — uses base_url
# ---------------------------------------------------------------------------


def test_skills_chat_stream_falls_back_to_base_url_when_no_agent_host(client_no_agent_host):
    """When agent_host is not set, stream_post falls back to the base_url http client."""
    captured = {}

    def fake_stream_post(path: str, *, json=None):
        captured["path"] = path
        captured["json"] = json
        yield 'data: {"type":"done","runId":"r1","threadId":"t1"}'

    # _agent_http should point to the same client as _http when no agent_host is set
    with patch.object(client_no_agent_host._agent_http, "stream_post", fake_stream_post):
        with client_no_agent_host.scopes.chat_stream(42, "Hi", model=MODEL) as stream:
            list(stream.text_stream)

    assert captured["path"] == "/agent/v1/scopes/42/runs"


# ---------------------------------------------------------------------------
# Config: agent_host stored in ModusConfig
# ---------------------------------------------------------------------------


def test_config_stores_agent_host():
    """ModusConfig must accept and normalize agent_host."""
    from modus._config import ModusConfig

    cfg = ModusConfig(api_key="modus_test", agent_host="https://agent.modus.com/")
    assert cfg.agent_host == "https://agent.modus.com"  # trailing slash stripped


def test_config_agent_host_none_by_default():
    from modus._config import ModusConfig

    cfg = ModusConfig(api_key="modus_test")
    assert cfg.agent_host is None


def test_client_accepts_agent_host():
    """Modus(agent_host=...) must wire through to config and _agent_http."""
    client = Modus(api_key="modus_test_key_abc123", agent_host="https://agent.modus.com")
    assert client._config.agent_host == "https://agent.modus.com"
    assert hasattr(client, "_agent_http")


def test_agent_host_from_env(monkeypatch):
    """MODUS_AGENT_HOST env var must be picked up when no explicit agent_host is given."""
    monkeypatch.setenv("MODUS_AGENT_HOST", "https://agent.staging.modus.com")
    client = Modus(api_key="modus_test_key_abc123")
    assert client._config.agent_host == "https://agent.staging.modus.com"


def test_explicit_agent_host_overrides_env(monkeypatch):
    monkeypatch.setenv("MODUS_AGENT_HOST", "https://agent.staging.modus.com")
    client = Modus(api_key="modus_test_key_abc123", agent_host="https://agent.custom.com")
    assert client._config.agent_host == "https://agent.custom.com"
