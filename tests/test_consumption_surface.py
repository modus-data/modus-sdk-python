"""Verify consumption client exposes only read surface."""
from modus import Modus


def test_skills_resource_has_no_create():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.scopes, "create"), \
        "skills.create must not exist in consumption SDK"


def test_skills_resource_has_no_update():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.scopes, "update")


def test_skills_resource_has_no_deploy():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.scopes, "deploy")


def test_skills_resource_has_no_delete():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.scopes, "delete")


def test_agents_resource_has_no_create():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.workflows, "create")


def test_agents_resource_has_no_update():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.workflows, "update")


def test_agents_resource_has_no_delete():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.workflows, "delete")


def test_context_resource_has_no_create_note():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.context, "create_note")


def test_context_items_has_no_update():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.context.items, "update")


def test_context_items_has_no_delete():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.context.items, "delete")


def test_skills_resource_has_list_and_get():
    client = Modus(api_key="modus_test_key")
    assert hasattr(client.scopes, "list")
    assert hasattr(client.scopes, "get")
    assert hasattr(client.scopes, "conversations")


def test_agents_resource_has_list_and_get():
    client = Modus(api_key="modus_test_key")
    assert hasattr(client.workflows, "list")
    assert hasattr(client.workflows, "get")


def test_context_items_has_list_and_get():
    client = Modus(api_key="modus_test_key")
    assert hasattr(client.context.items, "list")
    assert hasattr(client.context.items, "get")


def test_skills_resource_has_chat_and_context():
    client = Modus(api_key="modus_test_key")
    assert hasattr(client.scopes, "chat")
    assert hasattr(client.scopes, "chat_stream")
    assert hasattr(client.scopes, "get_context")


def test_modus_resource_has_chat_context_and_conversations():
    client = Modus(api_key="modus_test_key")
    assert hasattr(client.modus, "chat")
    assert hasattr(client.modus, "chat_stream")
    assert hasattr(client.modus, "get_context")
    assert hasattr(client.modus.conversations, "list")
    assert hasattr(client.modus.conversations, "get")


def test_agents_resource_has_runs():
    client = Modus(api_key="modus_test_key")
    assert hasattr(client.workflows.runs, "list")
    assert hasattr(client.workflows.runs, "get")


def test_agents_resource_has_chat_stream():
    client = Modus(api_key="modus_test_key")
    assert hasattr(client.workflows, "chat_stream")
