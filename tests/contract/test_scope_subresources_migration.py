import json
from dataclasses import replace

import httpx
import pytest
import respx
from modus._generated.models import SetSupervisionRequestDto
from modus.management.types.evaluations import UpdateEvaluationConfig
from pydantic import ValidationError

from .test_generated_wiring import _SAMPLES, BASE, _await_if, _client


@pytest.mark.parametrize("surface", ["consumption", "management"])
@pytest.mark.parametrize("is_async", [False, True])
async def test_scopes_constructor_rejects_removed_operations_mapping(surface, is_async) -> None:
    async with _client(surface, is_async) as client:
        resource = client.scopes
        args = [resource._http]
        if surface == "consumption":
            args.append(resource._agent_http)
        args.append(resource._config)
        with pytest.raises(TypeError, match="ops"):
            type(resource)(*args, ops={})


@pytest.mark.parametrize("is_async", [False, True])
async def test_interfaces_unwrap_validates_envelope_and_delete_discards_body(
    is_async: bool,
) -> None:
    async with _client("management", is_async) as client:
        resource = client.scopes.interfaces(42)
        with respx.mock(base_url=BASE) as router:
            listing = router.get("/api/v1/scopes/42/interfaces").mock(
                side_effect=[
                    httpx.Response(200, json={"interfaces": [_SAMPLES["ScopeInterface"]]}),
                    httpx.Response(200, json={}),
                ],
            )
            router.delete("/api/v1/scopes/42/interfaces/if-1").mock(
                return_value=httpx.Response(200, json={"deleted": True}),
            )
            rows = await _await_if(resource.list(), is_async)
            assert rows[0].scope_id == 1
            with pytest.raises(ValidationError):
                await _await_if(resource.list(), is_async)
            assert await _await_if(resource.delete("if-1"), is_async) is None
            assert listing.call_count == 2


@pytest.mark.parametrize("is_async", [False, True])
async def test_supervision_accepts_existing_keyword_and_sends_aliases(is_async: bool) -> None:
    async with _client("management", is_async) as client:
        with respx.mock(base_url=BASE) as router:
            route = router.route(method="PUT").mock(
                return_value=httpx.Response(200, json=_SAMPLES["Supervision"]),
            )
            resource = client.scopes.supervision(42)
            for method in (resource.set, resource.set_active):
                result = await _await_if(
                    method(supervision=SetSupervisionRequestDto(subordinate_agent_ids=[2])),
                    is_async,
                )
                assert result.subordinate_agent_ids == [2]
            assert [json.loads(call.request.content) for call in route.calls] == [
                {"subordinateAgentIds": [2]},
                {"subordinateAgentIds": [2]},
            ]


async def test_evaluation_update_keeps_existing_snake_case_dump() -> None:
    async with _client("management", False) as client:
        with respx.mock(base_url=BASE) as router:
            route = router.put("/api/v1/scopes/42/evaluations/config").mock(
                return_value=httpx.Response(200, json=_SAMPLES["EvaluationConfig"]),
            )
            client.scopes.evaluations(42).update_config(
                UpdateEvaluationConfig(judge_guidance="Be precise")
            )
            assert json.loads(route.calls[0].request.content) == {"judge_guidance": "Be precise"}


@pytest.mark.parametrize("is_async", [False, True])
async def test_conversation_constructor_operation_binding_applies_to_every_page(
    is_async: bool,
) -> None:
    async with _client("consumption", is_async) as client:
        original = client.scopes.conversations(42)
        resource = type(original)(
            original._http,
            original._config,
            42,
            ops=replace(original._ops, list="EvaluationsController_listRuns"),
        )
        with respx.mock(base_url=BASE) as router:
            route = router.get("/api/v1/scopes/42/evaluations/runs").mock(
                side_effect=[
                    httpx.Response(200, json={"conversations": [], "nextPageToken": "next"}),
                    httpx.Response(200, json={"conversations": [], "nextPageToken": ""}),
                ]
            )
            page = await _await_if(resource.list(source="slack", source_ref="channel"), is_async)
            await _await_if(page.get_next_page(), is_async)
            assert route.call_count == 2
            assert route.calls[1].request.url.params["pageToken"] == "next"


async def test_evaluation_constructor_operation_binding_is_preserved() -> None:
    async with _client("management", False) as client:
        original = client.scopes.evaluations(42)
        resource = type(original)(
            original._http,
            original._config,
            42,
            ops=replace(original._ops, get_config="ScopesController_get"),
        )
        with respx.mock(base_url=BASE) as router:
            route = router.get("/api/v1/scopes/42").mock(
                return_value=httpx.Response(200, json=_SAMPLES["EvaluationConfig"]),
            )
            assert resource.get_config().enabled is False
            assert route.called


@pytest.mark.parametrize("is_async", [False, True])
async def test_interface_delete_validates_scope_before_interface_id(is_async: bool) -> None:
    async with _client("management", is_async) as client:
        with respx.mock(base_url=BASE) as router:
            with pytest.raises(ValueError, match="scope_id"):
                await _await_if(client.scopes.interfaces("").delete(""), is_async)
            assert not router.calls


async def test_evaluation_get_run_validates_scope_before_run_id() -> None:
    async with _client("management", False) as client:
        with respx.mock(base_url=BASE) as router:
            with pytest.raises(ValueError, match="scope_id"):
                client.scopes.evaluations("").get_run("")
            assert not router.calls
