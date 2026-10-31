"""Context compose runs on the agent host, the host chat uses.

The agent host has no 30-second gateway limit, so a compose that takes longer
answers instead of failing with a bare 503.
"""

import json

import httpx
import pytest
import respx
from modus import AsyncModus, Modus, ModusError

COMPOSED = {
    "context": "## Tables",
    "contextItems": [],
    "originalCount": 3,
    "contextItemUids": ["ctx-1"],
    "selectedCount": 1,
    "sessionId": "sess-1",
}

HOSTS = [
    ("production default", {}, "https://agent.getmodus.com"),
    ("staging base_url", {"base_url": "https://api.staging.getmodus.com"}, "https://agent.staging.getmodus.com"),
    (
        "explicit agent_host",
        {"base_url": "http://localhost:3001", "agent_host": "http://localhost:3015"},
        "http://localhost:3015",
    ),
]


@pytest.mark.parametrize("_name,options,host", HOSTS)
def test_compose_calls_the_agent_host(_name, options, host, monkeypatch):
    monkeypatch.delenv("MODUS_AGENT_HOST", raising=False)
    monkeypatch.delenv("MODUS_BASE_URL", raising=False)
    client = Modus(api_key="modus_test_key", max_retries=0, **options)
    with respx.mock(assert_all_called=True) as router:
        scope = router.post(f"{host}/agent/v1/scopes/7/context").mock(
            return_value=httpx.Response(200, json=COMPOSED)
        )
        org = router.post(f"{host}/agent/v1/modus/context").mock(
            return_value=httpx.Response(200, json=COMPOSED)
        )
        assert client.scopes.get_context(7, "churn", limit=5).selected_count == 1
        assert client.modus.get_context("churn").context == "## Tables"
    assert json.loads(scope.calls.last.request.content) == {"message": "churn", "limit": 5}
    assert org.call_count == 1


@pytest.mark.parametrize("_name,options,host", HOSTS)
async def test_async_compose_calls_the_agent_host(_name, options, host, monkeypatch):
    monkeypatch.delenv("MODUS_AGENT_HOST", raising=False)
    monkeypatch.delenv("MODUS_BASE_URL", raising=False)
    async with AsyncModus(api_key="modus_test_key", max_retries=0, **options) as client:
        with respx.mock(assert_all_called=True) as router:
            router.post(f"{host}/agent/v1/scopes/7/context").mock(
                return_value=httpx.Response(200, json=COMPOSED)
            )
            router.post(f"{host}/agent/v1/modus/context").mock(
                return_value=httpx.Response(200, json=COMPOSED)
            )
            assert (await client.scopes.get_context(7, "churn")).selected_count == 1
            assert (await client.modus.get_context("churn")).session_id == "sess-1"


def test_compose_with_a_custom_base_url_and_no_agent_host_is_a_configuration_error(monkeypatch):
    monkeypatch.delenv("MODUS_AGENT_HOST", raising=False)
    client = Modus(api_key="modus_test_key", base_url="http://localhost:3001", max_retries=0)
    with respx.mock(assert_all_mocked=True) as router:
        with pytest.raises(ModusError, match="agent_host"):
            client.scopes.get_context(7, "churn")
        with pytest.raises(ModusError, match="agent_host"):
            client.modus.get_context("churn")
    assert router.calls.call_count == 0


async def test_async_compose_with_a_custom_base_url_and_no_agent_host_is_a_configuration_error(monkeypatch):
    monkeypatch.delenv("MODUS_AGENT_HOST", raising=False)
    async with AsyncModus(api_key="modus_test_key", base_url="http://localhost:3001", max_retries=0) as client:
        with respx.mock(assert_all_mocked=True) as router:
            with pytest.raises(ModusError, match="agent_host"):
                await client.scopes.get_context(7, "churn")
            with pytest.raises(ModusError, match="agent_host"):
                await client.modus.get_context("churn")
        assert router.calls.call_count == 0


def test_default_read_timeout_outwaits_the_server_compose_deadline():
    # The agent host stops a compose at 90 s with a 504. A shorter client read timeout would
    # abandon a compose still running and re-send it (compose is idempotent).
    server_compose_deadline_s = 90
    client = Modus(api_key="modus_test_key")
    assert client._config.timeout.read > server_compose_deadline_s
