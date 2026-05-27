"""Verify consumption client exposes only read surface."""
from modus import Modus


def test_skills_resource_has_no_create():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.skills, "create"), \
        "skills.create must not exist in consumption SDK"


def test_skills_resource_has_no_update():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.skills, "update")


def test_skills_resource_has_no_deploy():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.skills, "deploy")


def test_skills_resource_has_no_delete():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.skills, "delete")


def test_agents_resource_has_no_create():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.agents, "create")


def test_agents_resource_has_no_update():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.agents, "update")


def test_agents_resource_has_no_delete():
    client = Modus(api_key="modus_test_key")
    assert not hasattr(client.agents, "delete")


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
    assert hasattr(client.skills, "list")
    assert hasattr(client.skills, "get")
    assert hasattr(client.skills, "conversations")


def test_agents_resource_has_list_and_get():
    client = Modus(api_key="modus_test_key")
    assert hasattr(client.agents, "list")
    assert hasattr(client.agents, "get")


def test_context_items_has_list_and_get():
    client = Modus(api_key="modus_test_key")
    assert hasattr(client.context.items, "list")
    assert hasattr(client.context.items, "get")
