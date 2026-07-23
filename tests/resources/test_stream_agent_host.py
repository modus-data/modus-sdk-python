"""Tests: streaming chat methods must POST to agent-host runs paths.

Buffered chat (client.scopes.chat, client.modus.chat) stays on modus-api unchanged.
Streaming (client.scopes.chat_stream, client.modus.chat_stream,
           client.workflows.chat_stream) POSTs to:

  skills  → {agent_host}/agent/v1/scopes/{id}/runs
  modus   → {agent_host}/agent/v1/modus/runs
  agents  → {agent_host}/agent/v1/workflows/{id}/runs

Body format:
  { "message": "...", "sessionId": "<thread or uuid>", "config": { "model": "..." } }
  (version omitted unless explicitly passed)
"""

from __future__ import annotations

from unittest.mock import patch
from uuid import UUID

import pytest
from modus import Modus
from modus._config import DEFAULT_AGENT_HOST

API_BASE = "https://api.getmodus.com"
AGENT_HOST = "https://agent.example.com"
MODEL = "claude-sonnet-5"


@pytest.fixture
def client_with_agent_host() -> Modus:
    return Modus(api_key="modus_test_key_abc123", base_url=API_BASE, agent_host=AGENT_HOST)


@pytest.fixture
def client_default_hosts() -> Modus:
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
    assert "sessionId" in captured["json"]
    UUID(captured["json"]["sessionId"])  # always a UUID when thread_id omitted


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


def test_skills_chat_stream_blank_thread_id_mints_session_id(client_with_agent_host):
    """Blank thread_id still sends a minted sessionId."""
    captured = {}

    def fake_stream_post(path: str, *, json=None):
        captured["json"] = json
        yield 'data: {"type":"done","runId":"r1","threadId":"t-new"}'

    with patch.object(client_with_agent_host._agent_http, "stream_post", fake_stream_post):
        with client_with_agent_host.scopes.chat_stream(
            42, "Hi", model=MODEL, thread_id="  "
        ) as stream:
            list(stream.text_stream)

    UUID(captured["json"]["sessionId"])


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


def test_skills_chat_stream_includes_organization_id_when_configured():
    client = Modus(
        api_key="modus_test_key_abc123",
        base_url=API_BASE,
        agent_host=AGENT_HOST,
        organization_id="org_test",
    )
    captured = {}

    def fake_stream_post(path: str, *, json=None):
        captured["json"] = json
        yield 'data: {"type":"done","runId":"r1","threadId":"t1"}'

    with patch.object(client._agent_http, "stream_post", fake_stream_post):
        with client.scopes.chat_stream(42, "Hi", model=MODEL) as stream:
            list(stream.text_stream)

    assert captured["json"]["organizationId"] == "org_test"


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
    UUID(captured["json"]["sessionId"])


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
# Default agent host
# ---------------------------------------------------------------------------


def test_skills_chat_stream_defaults_to_production_agent_host(client_default_hosts):
    """When agent_host is not set, client uses DEFAULT_AGENT_HOST."""
    assert client_default_hosts._config.agent_host == DEFAULT_AGENT_HOST
    assert client_default_hosts._agent_http.config.base_url == DEFAULT_AGENT_HOST

    captured = {}

    def fake_stream_post(path: str, *, json=None):
        captured["path"] = path
        captured["json"] = json
        yield 'data: {"type":"done","runId":"r1","threadId":"t1"}'

    with patch.object(client_default_hosts._agent_http, "stream_post", fake_stream_post):
        with client_default_hosts.scopes.chat_stream(42, "Hi", model=MODEL) as stream:
            list(stream.text_stream)

    assert captured["path"] == "/agent/v1/scopes/42/runs"


# ---------------------------------------------------------------------------
# Config: agent_host stored in ModusConfig
# ---------------------------------------------------------------------------


def test_config_stores_agent_host():
    """ModusConfig must accept and normalize agent_host."""
    from modus._config import ModusConfig

    cfg = ModusConfig(api_key="modus_test", agent_host="https://agent.getmodus.com/")
    assert cfg.agent_host == "https://agent.getmodus.com"  # trailing slash stripped


def test_config_agent_host_none_by_default():
    from modus._config import ModusConfig

    cfg = ModusConfig(api_key="modus_test")
    assert cfg.agent_host is None


def test_client_defaults_agent_host():
    """Modus() without agent_host uses DEFAULT_AGENT_HOST."""
    client = Modus(api_key="modus_test_key_abc123")
    assert client._config.agent_host == DEFAULT_AGENT_HOST
    assert client._agent_http.config.base_url == DEFAULT_AGENT_HOST


def test_base_urls_agent_service_drives_streaming_host():
    """base_urls['agent-service'] must set the streaming client origin (TS parity)."""
    client = Modus(
        api_key="modus_test_key_abc123",
        base_urls={"agent-service": "http://localhost:3130/"},
    )
    assert client._config.agent_host == "http://localhost:3130"
    assert client._agent_http.config.base_url == "http://localhost:3130"


def test_agent_host_from_env(monkeypatch):
    """MODUS_AGENT_HOST env var must be picked up when no explicit agent_host is given."""
    monkeypatch.setenv("MODUS_AGENT_HOST", "https://agent.staging.getmodus.com")
    client = Modus(api_key="modus_test_key_abc123")
    assert client._config.agent_host == "https://agent.staging.getmodus.com"


def test_explicit_agent_host_overrides_env(monkeypatch):
    monkeypatch.setenv("MODUS_AGENT_HOST", "https://agent.staging.getmodus.com")
    client = Modus(api_key="modus_test_key_abc123", agent_host="https://agent.custom.com")
    assert client._config.agent_host == "https://agent.custom.com"
