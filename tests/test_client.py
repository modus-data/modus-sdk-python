"""Tests for Modus and AsyncModus client initialization."""

import pytest
from modus import AsyncModus, Modus
from modus._exceptions import AuthenticationError


def test_sync_client_init(monkeypatch):
    monkeypatch.delenv("MODUS_BASE_URL", raising=False)
    client = Modus(api_key="modus_testkey")
    assert repr(client) == "Modus(base_url='https://api.getmodus.com')"


def test_sync_client_from_env(monkeypatch):
    monkeypatch.setenv("MODUS_API_KEY", "modus_envkey")
    client = Modus()
    assert client is not None


def test_sync_client_no_key_raises(monkeypatch):
    monkeypatch.delenv("MODUS_API_KEY", raising=False)
    with pytest.raises(AuthenticationError):
        Modus()


def test_sync_client_bad_key_raises():
    with pytest.raises(AuthenticationError):
        Modus(api_key="not-a-modus-key")


def test_sync_client_custom_base_url():
    client = Modus(api_key="modus_test", base_url="http://localhost:3080")
    assert "localhost:3080" in repr(client)


def test_sync_client_has_scopes():
    client = Modus(api_key="modus_test")
    assert hasattr(client, "scopes")
    assert hasattr(client.scopes, "list")
    assert hasattr(client.scopes, "get")
    assert hasattr(client.scopes, "conversations")


def test_sync_client_has_chat_not_old_run_stubs():
    """run()/stream() stubs are not on the public surface; use chat/chat_stream."""
    client = Modus(api_key="modus_test")
    assert not hasattr(client.scopes, "run")
    assert not hasattr(client.scopes, "stream")


def test_sync_client_exposes_chat_and_runs():
    client = Modus(api_key="modus_test")
    assert hasattr(client.scopes, "chat")
    assert hasattr(client.scopes, "chat_stream")
    assert hasattr(client.scopes, "get_context")
    assert hasattr(client.workflows, "runs")


def test_sync_client_has_workflows():
    client = Modus(api_key="modus_test")
    assert hasattr(client, "workflows")
    assert hasattr(client.workflows, "list")
    assert hasattr(client.workflows, "get")


def test_sync_client_has_context():
    client = Modus(api_key="modus_test")
    assert hasattr(client, "context")
    assert hasattr(client.context, "items")
    assert hasattr(client.context.items, "list")
    assert hasattr(client.context.items, "get")


def test_sync_client_has_scopes_and_workflows_aliases():
    """Additive /scopes + /workflows accessors alias skills + agents."""
    client = Modus(api_key="modus_test")
    assert hasattr(client, "scopes")
    assert hasattr(client.scopes, "list")
    assert hasattr(client.scopes, "get")
    assert hasattr(client.scopes, "chat")
    assert hasattr(client.scopes, "chat_stream")
    assert hasattr(client.scopes, "conversations")
    assert hasattr(client, "workflows")
    assert hasattr(client.workflows, "list")
    assert hasattr(client.workflows, "get")
    assert hasattr(client.workflows.runs, "list")


def test_async_client_has_scopes_and_workflows_aliases():
    client = AsyncModus(api_key="modus_test")
    assert hasattr(client, "scopes")
    assert hasattr(client.scopes, "chat_stream")
    assert hasattr(client, "workflows")
    assert hasattr(client.workflows, "runs")


def test_base_url_from_env(monkeypatch):
    monkeypatch.setenv("MODUS_BASE_URL", "http://localhost:3080")
    client = Modus(api_key="modus_testkey")
    assert "localhost:3080" in repr(client)


def test_explicit_base_url_takes_precedence_over_env(monkeypatch):
    monkeypatch.setenv("MODUS_BASE_URL", "http://localhost:3080")
    client = Modus(api_key="modus_testkey", base_url="http://localhost:9999")
    assert "9999" in repr(client)


def test_async_client_init(monkeypatch):
    monkeypatch.delenv("MODUS_BASE_URL", raising=False)
    client = AsyncModus(api_key="modus_testkey")
    assert repr(client) == "AsyncModus(base_url='https://api.getmodus.com')"


def test_async_base_url_from_env(monkeypatch):
    monkeypatch.setenv("MODUS_BASE_URL", "http://localhost:3080")
    client = AsyncModus(api_key="modus_testkey")
    assert "localhost:3080" in repr(client)


def test_context_manager():
    with Modus(api_key="modus_test") as client:
        assert client is not None


@pytest.mark.asyncio
async def test_async_context_manager():
    async with AsyncModus(api_key="modus_test") as client:
        assert client is not None
