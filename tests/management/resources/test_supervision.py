import httpx
import respx
from modus._generated.models import SetSupervisionRequestDto


@respx.mock
def test_supervision_get_and_set(client) -> None:
    url = "https://api.modus.com/api/v1/scopes/42/supervision"
    respx.get(url).mock(return_value=httpx.Response(
        200, json={"supervisorAgentId": 42, "subordinateAgentIds": [17]},
    ))
    route = respx.put(url).mock(return_value=httpx.Response(
        200, json={"supervisorAgentId": 42, "subordinateAgentIds": [18]},
    ))
    assert client.scopes.supervision(42).get().subordinate_agent_ids == [17]
    assert client.scopes.supervision(42).set(
        SetSupervisionRequestDto(subordinate_agent_ids=[18])
    ).subordinate_agent_ids == [18]
    assert route.called
