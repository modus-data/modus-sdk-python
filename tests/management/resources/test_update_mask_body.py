"""PATCH with ``update_mask`` sends only what the caller set, plus null for masked fields left unset.

Before the fix every unset field went on the wire as ``null`` whenever a mask was given, and the
server's DTO validators rejected the unmasked nulls (staging: ``interfaces must be an array``).
"""

from __future__ import annotations

import json
from typing import Any, Callable

import httpx
import pytest
import respx
from modus._generated.models import UpdateAgentInterfaceDto

BASE = "https://api.modus.com/api/v1"
UID = "7a3f9d2c-1111-4000-a000-000000000abc"

_SCOPE = {
    "id": 10, "slug": "s", "name": "S", "status": "draft", "description": None,
    "orgUuid": "org", "hasUnpublishedChanges": True, "activeVariationId": None,
    "draftVariationId": "v", "accessConfig": {"visibility": "shared", "groupPermissions": {},
    "guardrails": [], "sharedWith": []}, "createdAt": "2026-01-01T00:00:00Z",
    "updatedAt": "2026-01-01T00:00:00Z", "deletedAt": None,
    "canManage": True, "canUse": True, "manageDenial": None,
}
_WORKFLOW = {**_SCOPE, "type": "workflow", "isEnabled": False}
_INTERFACE = {
    "id": "int_1", "agentId": 10, "type": "mcp", "name": "Internal", "config": {},
    "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z",
}


def _mock_scope() -> respx.Route:
    return respx.patch(url__regex=rf"{BASE}/scopes/10(\?.*)?$").mock(
        return_value=httpx.Response(200, json=_SCOPE))


def _mock_workflow() -> respx.Route:
    return respx.patch(url__regex=rf"{BASE}/workflows/10(\?.*)?$").mock(
        return_value=httpx.Response(200, json=_WORKFLOW))


def _mock_interface() -> respx.Route:
    return respx.patch(url__regex=rf"{BASE}/workflows/10/interfaces/int_1(\?.*)?$").mock(
        return_value=httpx.Response(200, json=_INTERFACE))


def _mock_item(sample_context_item: dict) -> respx.Route:
    respx.get(f"{BASE}/context/items/{UID}").mock(
        return_value=httpx.Response(200, json=sample_context_item))
    return respx.patch(url__regex=rf"{BASE}/context/items/{UID}(\?.*)?$").mock(
        return_value=httpx.Response(200, json={"uid": UID}))


# (mock, call, expected body) per resource. Each call sets one field and masks it plus one
# field it leaves unset, so the body must hold exactly those two keys.
_CASES: dict[str, tuple[Callable[..., respx.Route], Callable[[Any], Any], dict]] = {
    "scopes": (
        lambda _: _mock_scope(),
        lambda c: c.scopes.update(10, name="n", update_mask="name,description"),
        {"name": "n", "description": None},
    ),
    "workflows": (
        lambda _: _mock_workflow(),
        lambda c: c.workflows.update(10, name="n", update_mask="name,description"),
        {"name": "n", "description": None},
    ),
    "workflow interfaces": (
        lambda _: _mock_interface(),
        lambda c: c.workflows.interfaces(10).update(
            "int_1", UpdateAgentInterfaceDto(name="n"), update_mask="name,config"),
        {"name": "n", "config": None},
    ),
    "context items": (
        _mock_item,
        lambda c: c.context.items.update(UID, description="d", update_mask="description,topics"),
        {"description": "d", "topics": None},
    ),
}


@pytest.mark.parametrize("resource", list(_CASES))
@respx.mock
def test_update_mask_body_holds_only_set_and_masked_fields(client, sample_context_item, resource):
    mock, call, expected = _CASES[resource]
    route = mock(sample_context_item)
    call(client)
    assert json.loads(route.calls.last.request.content) == expected


@pytest.mark.parametrize("resource", list(_CASES))
@respx.mock
async def test_async_update_mask_body_holds_only_set_and_masked_fields(
    async_client, sample_context_item, resource
):
    mock, call, expected = _CASES[resource]
    route = mock(sample_context_item)
    await call(async_client)
    assert json.loads(route.calls.last.request.content) == expected


@respx.mock
def test_update_mask_nested_path_does_not_null_the_root(client):
    """``accessConfig.visibility`` names a nested path; nulling the root would wipe the object."""
    route = _mock_scope()
    client.scopes.update(10, name="n", update_mask="name,accessConfig.visibility")
    assert json.loads(route.calls.last.request.content) == {"name": "n"}
