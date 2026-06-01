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
    assert hasattr(client.skills, "list")
    assert hasattr(client.skills, "get")
    assert hasattr(client.skills, "create")
    assert hasattr(client.skills, "update")
    assert hasattr(client.skills, "deploy")
    assert hasattr(client.skills, "delete")
    assert hasattr(client.skills, "conversations")


def test_client_has_agents_resource():
    client = ModusManagement(api_key="modus_test_key")
    assert hasattr(client.agents, "list")
    assert hasattr(client.agents, "create")
    assert hasattr(client.agents, "deploy")


def test_client_has_context_resource():
    client = ModusManagement(api_key="modus_test_key")
    assert hasattr(client.context, "create_note")
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
