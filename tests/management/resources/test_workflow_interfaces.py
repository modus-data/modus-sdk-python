import httpx
import respx
from modus._generated.models import AddAgentInterfaceDto

BASE = "https://api.modus.com/api/v1/workflows/42"
INTERFACE = {
    "id": "int_1", "agentId": 42, "type": "mcp", "name": "Internal",
    "config": {}, "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z",
}


@respx.mock
def test_workflow_interfaces_list_and_create(client) -> None:
    respx.get(f"{BASE}/interfaces").mock(
        return_value=httpx.Response(200, json={"interfaces": [INTERFACE], "nextPageToken": None}),
    )
    created = respx.post(f"{BASE}/interfaces").mock(return_value=httpx.Response(201, json=INTERFACE))
    assert client.workflows.interfaces(42).list()[0].id == "int_1"
    assert client.workflows.interfaces(42).create(
        AddAgentInterfaceDto(type="mcp", name="Internal")
    ).id == "int_1"
    assert created.called
