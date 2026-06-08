"""Tests for guardrails accessConfig wire helpers."""

from modus.management.types._guardrails_access import (
    access_config_wire_for_create,
    access_config_wire_for_update,
)


def test_access_config_wire_for_create_includes_required_fields():
    payload = access_config_wire_for_create(["no-pii"])
    assert payload["visibility"] == "shared"
    assert payload["guardrails"] == ["no-pii"]
    assert payload["sharedWith"] == []
    assert payload["groupPermissions"]["__everyone__"] == {"use": True, "manage": True}
    assert "permissions" not in payload


def test_access_config_wire_for_update_preserves_existing_acl():
    existing = {
        "visibility": "private",
        "groupPermissions": {},
        "guardrails": [],
        "sharedWith": [{"email": "alice@example.com"}],
        "ownerUserId": "user_abc",
    }
    payload = access_config_wire_for_update(existing, ["no-pii"])
    assert payload["visibility"] == "private"
    assert payload["sharedWith"] == [{"email": "alice@example.com"}]
    assert payload["guardrails"] == ["no-pii"]
