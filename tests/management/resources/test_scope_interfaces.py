import httpx
import respx
from modus._generated.models import AddScopeInterfaceDto, UpdateScopeInterfaceDto

BASE = "https://api.modus.com/api/v1/scopes/42"
IFACE_ID = "00000000-0000-4000-a000-000000000500"
INTERFACE = {
    "id": IFACE_ID, "scopeId": 42, "type": "slack", "name": "Slack",
    "config": {"accessMode": "all"},
    "createdAt": "2026-09-30T00:00:00Z", "updatedAt": "2026-09-30T00:00:00Z",
}


@respx.mock
def test_scope_interfaces_list_and_create(client) -> None:
    respx.get(f"{BASE}/interfaces").mock(
        return_value=httpx.Response(200, json={"interfaces": [INTERFACE]}),
    )
    created = respx.post(f"{BASE}/interfaces").mock(return_value=httpx.Response(201, json=INTERFACE))
    assert client.scopes.interfaces(42).list()[0].id == IFACE_ID
    assert client.scopes.interfaces(42).create({"type": "slack"}).scope_id == 42
    assert created.called


@respx.mock
def test_scope_interfaces_update_and_delete(client) -> None:
    patched = respx.patch(f"{BASE}/interfaces/{IFACE_ID}").mock(return_value=httpx.Response(200, json=INTERFACE))
    deleted = respx.delete(f"{BASE}/interfaces/{IFACE_ID}").mock(return_value=httpx.Response(204))
    client.scopes.interfaces(42).update(IFACE_ID, UpdateScopeInterfaceDto(name="Support"), update_mask="name")
    client.scopes.interfaces(42).delete(IFACE_ID)
    assert patched.calls.last.request.url.params["updateMask"] == "name"
    assert deleted.called


@respx.mock
async def test_async_scope_interfaces_create(async_client) -> None:
    respx.post(f"{BASE}/interfaces").mock(return_value=httpx.Response(201, json=INTERFACE))
    created = await async_client.scopes.interfaces(42).create(AddScopeInterfaceDto(type="slack"))
    assert created.type == "slack"


@respx.mock
def test_scope_interfaces_update_with_mask_sends_no_nulls(client) -> None:
    import json

    from modus._generated.models import ChatInterfaceConfigDto

    patched = respx.patch(f"{BASE}/interfaces/{IFACE_ID}").mock(return_value=httpx.Response(200, json=INTERFACE))
    client.scopes.interfaces(42).update(
        IFACE_ID,
        UpdateScopeInterfaceDto(config=ChatInterfaceConfigDto(access_mode="all")),
        update_mask="name,config",
    )
    assert json.loads(patched.calls.last.request.content) == {"config": {"accessMode": "all"}}
