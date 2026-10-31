"""Agent host resolution: chat and runs go to the agent host, never to production by default."""

from __future__ import annotations

import httpx
import pytest
import respx
from modus import AsyncModus, Modus, ModusError

PROD_AGENT_HOST = "https://agent.getmodus.com"


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
    """Modus() with the default base URL derives the production agent host."""
    client = Modus(api_key="modus_test_key_abc123")
    assert client._config.agent_host == PROD_AGENT_HOST


def test_base_urls_agent_service_drives_streaming_host():
    """base_urls['agent-service'] must set the streaming client origin (TS parity)."""
    client = Modus(
        api_key="modus_test_key_abc123",
        base_urls={"agent-service": "http://localhost:3130/"},
    )
    assert client._config.agent_host == "http://localhost:3130"


def test_agent_host_from_env(monkeypatch):
    """MODUS_AGENT_HOST env var must be picked up when no explicit agent_host is given."""
    monkeypatch.setenv("MODUS_AGENT_HOST", "https://agent.staging.getmodus.com")
    client = Modus(api_key="modus_test_key_abc123")
    assert client._config.agent_host == "https://agent.staging.getmodus.com"


def test_agent_host_derived_from_staging_base_url(monkeypatch):
    """api.staging… base_url alone should select agent.staging… (no MODUS_AGENT_HOST)."""
    monkeypatch.delenv("MODUS_AGENT_HOST", raising=False)
    client = Modus(
        api_key="modus_test_key_abc123",
        base_url="https://api.staging.getmodus.com",
    )
    assert client._config.agent_host == "https://agent.staging.getmodus.com"


def test_agent_host_not_derived_from_custom_api_host(monkeypatch):
    """Custom api.* origins get no agent host rather than production's."""
    monkeypatch.delenv("MODUS_AGENT_HOST", raising=False)
    client = Modus(
        api_key="modus_test_key_abc123",
        base_url="https://api.attacker.example",
    )
    assert client._config.agent_host is None
    with pytest.raises(ModusError, match="agent_host"):
        client.modus.chat("x", model="claude-sonnet-5")


def test_explicit_agent_host_overrides_env(monkeypatch):
    monkeypatch.setenv("MODUS_AGENT_HOST", "https://agent.staging.getmodus.com")
    client = Modus(api_key="modus_test_key_abc123", agent_host="https://agent.custom.com")
    assert client._config.agent_host == "https://agent.custom.com"


# ---------------------------------------------------------------------------
# Chat against a non-Modus base_url (localhost, Modus Core, a custom domain)
# ---------------------------------------------------------------------------

LOCAL_API = "http://localhost:3040"
LOCAL_AGENT = "http://localhost:3130"
_DONE = 'data: {"type": "done", "runId": "r1", "threadId": "t1", "content": "ok"}\n\n'


@pytest.mark.parametrize("via_env", [False, True])
@respx.mock
def test_chat_uses_the_configured_agent_host_for_a_custom_base_url(monkeypatch, via_env):
    monkeypatch.delenv("MODUS_AGENT_HOST", raising=False)
    if via_env:
        monkeypatch.setenv("MODUS_AGENT_HOST", LOCAL_AGENT)
    route = respx.post(f"{LOCAL_AGENT}/agent/v1/modus/runs").mock(
        return_value=httpx.Response(200, text=_DONE, headers={"Content-Type": "text/event-stream"})
    )
    client = Modus(
        api_key="modus_test_key_abc123",
        base_url=LOCAL_API,
        **({} if via_env else {"agent_host": LOCAL_AGENT}),
    )

    assert client.modus.chat("x", model="claude-sonnet-5").result().content == "ok"
    assert route.called


@pytest.mark.parametrize("env_value", [None, "", "  "])
@respx.mock
def test_chat_without_an_agent_host_refuses_before_any_request(monkeypatch, env_value):
    monkeypatch.delenv("MODUS_AGENT_HOST", raising=False)
    if env_value is not None:
        monkeypatch.setenv("MODUS_AGENT_HOST", env_value)
    client = Modus(api_key="modus_test_key_abc123", base_url=LOCAL_API)

    with pytest.raises(ModusError, match="agent_host"):
        client.scopes.chat(1, "x", model="claude-sonnet-5").result()
    assert respx.calls.call_count == 0


@respx.mock
async def test_async_chat_without_an_agent_host_refuses_before_any_request(monkeypatch):
    monkeypatch.delenv("MODUS_AGENT_HOST", raising=False)
    client = AsyncModus(api_key="modus_test_key_abc123", base_url=LOCAL_API)

    with pytest.raises(ModusError, match="agent_host"):
        await client.scopes.chat(1, "x", model="claude-sonnet-5")
    assert respx.calls.call_count == 0
