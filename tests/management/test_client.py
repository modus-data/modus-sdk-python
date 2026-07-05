"""Tests for ModusManagement client instantiation."""

import pytest
from modus._exceptions import AuthenticationError
from modus.management import AsyncModusManagement, ModusManagement


def test_client_instantiates(monkeypatch):
    monkeypatch.delenv("MODUS_BASE_URL", raising=False)
    client = ModusManagement(api_key="modus_test_key")
    assert repr(client) == "ModusManagement(base_url='https://api.modus.com')"


def test_client_has_skills_resource():
    client = ModusManagement(api_key="modus_test_key")
    assert hasattr(client.scopes, "list")
    assert hasattr(client.scopes, "get")
    assert hasattr(client.scopes, "create")
    assert hasattr(client.scopes, "update")
    assert hasattr(client.scopes, "deploy")
    assert hasattr(client.scopes, "delete")
    assert hasattr(client.scopes, "conversations")


def test_client_has_agents_resource():
    client = ModusManagement(api_key="modus_test_key")
    assert hasattr(client.workflows, "list")
    assert hasattr(client.workflows, "create")
    assert hasattr(client.workflows, "deploy")


def test_client_has_scopes_and_workflows_aliases():
    """Additive /scopes + /workflows management accessors alias skills + agents."""
    client = ModusManagement(api_key="modus_test_key")
    assert hasattr(client, "scopes")
    assert hasattr(client.scopes, "create")
    assert hasattr(client.scopes, "deploy")
    assert hasattr(client.scopes, "memories")
    assert hasattr(client.scopes, "conversations")
    assert hasattr(client, "workflows")
    assert hasattr(client.workflows, "create")
    assert hasattr(client.workflows, "deploy")


def test_async_client_has_scopes_and_workflows_aliases():
    client = AsyncModusManagement(api_key="modus_test_key")
    assert hasattr(client, "scopes")
    assert hasattr(client.scopes, "create")
    assert hasattr(client, "workflows")
    assert hasattr(client.workflows, "create")


def test_client_has_context_resource():
    client = ModusManagement(api_key="modus_test_key")
    assert hasattr(client.context, "create_note")
    assert hasattr(client.context, "update_note")
    assert hasattr(client.context, "update_link")
    assert hasattr(client.context, "update_saved_query")
    assert hasattr(client.context, "create_saved_query")
    assert hasattr(client.context.items, "list")
    assert hasattr(client.context.items, "update")
    assert hasattr(client.context.items, "delete")


def test_client_raises_on_missing_key(monkeypatch):
    monkeypatch.delenv("MODUS_API_KEY", raising=False)
    with pytest.raises(AuthenticationError, match="No API key provided"):
        ModusManagement()


def test_client_raises_on_bad_key_format():
    with pytest.raises(AuthenticationError, match="Invalid API key format"):
        ModusManagement(api_key="sk-wrong-format")


def test_async_client_instantiates(monkeypatch):
    monkeypatch.delenv("MODUS_BASE_URL", raising=False)
    client = AsyncModusManagement(api_key="modus_test_key")
    assert repr(client) == "AsyncModusManagement(base_url='https://api.modus.com')"
