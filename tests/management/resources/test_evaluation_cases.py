"""Client-assigned evaluation case ids survive a retry as the same body."""

import json
import re

import httpx
import pytest
import respx
from modus import ConflictError
from modus.management import ModusManagement

BASE = "https://api.modus.com"
UUID_V4 = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _client(*, max_retries: int = 0) -> ModusManagement:
    return ModusManagement(api_key="modus_test_key", base_url=BASE, max_retries=max_retries)


@respx.mock
def test_add_case_without_id_sends_a_generated_id():
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(201, json=json.loads(request.content))

    route = respx.post(f"{BASE}/api/v1/scopes/42/evaluations/cases").mock(side_effect=respond)
    added = _client(max_retries=0).scopes.evaluations(42).add_case(
        task="t", expected_output="o"
    )
    body = json.loads(route.calls[0].request.content)
    assert UUID_V4.match(body["id"])
    assert body["task"] == "t"
    assert body["expectedOutput"] == "o"
    assert added.id == body["id"]


@respx.mock
async def test_async_client_has_scope_evaluations(async_client):
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(201, json=json.loads(request.content))

    route = respx.post(f"{BASE}/api/v1/scopes/42/evaluations/cases").mock(side_effect=respond)
    respx.delete(f"{BASE}/api/v1/scopes/42/evaluations/cases/c1").mock(
        return_value=httpx.Response(204)
    )
    respx.get(f"{BASE}/api/v1/scopes/42/evaluations/config").mock(
        return_value=httpx.Response(200, json={
            "enabled": True,
            "notifications": {"recipients": [], "channels": {"email": False}},
        })
    )
    evaluations = async_client.scopes.evaluations(42)
    added = await evaluations.add_case(task="t", expected_output="o", id="c1")
    assert added.id == "c1"
    assert json.loads(route.calls[0].request.content)["id"] == "c1"
    assert await evaluations.delete_case("c1") is None
    config = await evaluations.get_config()
    assert config.enabled is True


@respx.mock
def test_retried_add_case_sends_the_same_body_and_surfaces_409():
    bodies: list[dict[str, str]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        if len(bodies) == 1:
            return httpx.Response(
                429, json={"error": {"message": "slow down"}}, headers={"retry-after": "0"}
            )
        return httpx.Response(
            409,
            json={"error": {"message": "An evaluation case with this id already exists."}},
        )

    respx.post(f"{BASE}/api/v1/scopes/42/evaluations/cases").mock(side_effect=respond)
    with pytest.raises(ConflictError):
        _client(max_retries=1).scopes.evaluations(42).add_case(task="t", expected_output="o")
    assert len(bodies) == 2
    assert UUID_V4.match(bodies[0]["id"])
    assert bodies[1] == bodies[0]
