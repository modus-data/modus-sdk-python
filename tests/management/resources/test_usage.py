"""Tests for mgmt.usage.list."""

import httpx
import pytest
import respx
from modus.management import AsyncModusManagement, ModusManagement
from modus.management.types.usage import UsageReport, UsageUsersReport

BASE = "https://api.modus.com"

USAGE_RESP = {
    "org_id": "org_abc123",
    "since": "2026-05-01T00:00:00.000Z",
    "until": "2026-05-08T00:00:00.000Z",
    "rollup": "hour",
    "groupBy": "model",
    "buckets": [
        {
            "bucket": "2026-05-01T00:00:00.000Z",
            "model": "claude-sonnet-4-5",
            "groupValue": "claude-sonnet-4-5",
            "callCount": 12,
            "inputTokens": 4000,
            "outputTokens": 900,
            "credits": 1.2,
        }
    ],
    "totals": {
        "callCount": 12,
        "inputTokens": 4000,
        "outputTokens": 900,
        "credits": 1.2,
    },
}

USAGE_BY_SKILL_RESP = {
    "org_id": "org_abc123",
    "since": "2026-05-01T00:00:00.000Z",
    "until": "2026-05-08T00:00:00.000Z",
    "rollup": "day",
    "groupBy": "skill",
    "buckets": [
        {
            "bucket": "2026-05-01T00:00:00.000Z",
            "groupValue": "42",
            "callCount": 3,
            "inputTokens": 900,
            "outputTokens": 120,
            "credits": 0.4,
        }
    ],
    "totals": {
        "callCount": 3,
        "inputTokens": 900,
        "outputTokens": 120,
        "credits": 0.4,
    },
}


def _client():
    return ModusManagement(api_key="modus_test_key", base_url=BASE)


@respx.mock
def test_usage_list():
    route = respx.get(f"{BASE}/api/v1/usage").mock(
        return_value=httpx.Response(200, json=USAGE_RESP)
    )
    report = _client().usage.list(
        since="2026-05-01T00:00:00.000Z",
        until="2026-05-08T00:00:00.000Z",
        rollup="hour",
    )
    assert isinstance(report, UsageReport)
    assert report.org_id == "org_abc123"
    assert len(report.buckets) == 1
    assert report.buckets[0].model == "claude-sonnet-4-5"
    params = dict(route.calls[0].request.url.params)
    assert params["since"] == "2026-05-01T00:00:00.000Z"
    assert params["until"] == "2026-05-08T00:00:00.000Z"
    assert params["rollup"] == "hour"


@respx.mock
@pytest.mark.asyncio
async def test_usage_list_async():
    route = respx.get(f"{BASE}/api/v1/usage").mock(
        return_value=httpx.Response(200, json=USAGE_RESP)
    )
    async with AsyncModusManagement(api_key="modus_test_key", base_url=BASE) as client:
        report = await client.usage.list(
            since="2026-05-01T00:00:00.000Z",
            until="2026-05-08T00:00:00.000Z",
            rollup="day",
        )
    assert report.org_id == "org_abc123"
    params = dict(route.calls[0].request.url.params)
    assert params["since"] == "2026-05-01T00:00:00.000Z"
    assert params["until"] == "2026-05-08T00:00:00.000Z"
    assert params["rollup"] == "day"


@respx.mock
def test_usage_list_skill_grouping_omits_model():
    """Skill/agent breakdown buckets omit model; group_value carries the dimension."""
    respx.get(f"{BASE}/api/v1/usage").mock(
        return_value=httpx.Response(200, json=USAGE_BY_SKILL_RESP)
    )
    report = _client().usage.list(
        since="2026-05-01T00:00:00.000Z",
        until="2026-05-08T00:00:00.000Z",
        rollup="day",
    )
    assert len(report.buckets) == 1
    bucket = report.buckets[0]
    assert bucket.model is None
    assert bucket.group_value == "42"


@respx.mock
def test_usage_list_forwards_repeated_user_email_params():
    route = respx.get(f"{BASE}/api/v1/usage").mock(
        return_value=httpx.Response(200, json=USAGE_RESP)
    )
    _client().usage.list(
        since="2026-05-01T00:00:00.000Z",
        until="2026-05-08T00:00:00.000Z",
        rollup="hour",
        user_email=["jane@acme.com", "john@acme.com"],
    )
    params = route.calls[0].request.url.params
    assert params.get_list("user_email") == ["jane@acme.com", "john@acme.com"]


@respx.mock
def test_usage_list_users():
    route = respx.get(f"{BASE}/api/v1/usage/users").mock(
        return_value=httpx.Response(200, json={"users": [{"email": "jane@acme.com"}]})
    )
    report = _client().usage.list_users(
        since="2026-05-01T00:00:00.000Z",
        until="2026-05-08T00:00:00.000Z",
    )
    assert isinstance(report, UsageUsersReport)
    assert report.users[0].email == "jane@acme.com"
    params = dict(route.calls[0].request.url.params)
    assert params["since"] == "2026-05-01T00:00:00.000Z"
    assert params["until"] == "2026-05-08T00:00:00.000Z"


@respx.mock
@pytest.mark.asyncio
async def test_usage_list_users_async():
    respx.get(f"{BASE}/api/v1/usage/users").mock(
        return_value=httpx.Response(200, json={"users": [{"email": "jane@acme.com"}]})
    )
    async with AsyncModusManagement(api_key="modus_test_key", base_url=BASE) as client:
        report = await client.usage.list_users(
            since="2026-05-01T00:00:00.000Z",
            until="2026-05-08T00:00:00.000Z",
        )
    assert report.users[0].email == "jane@acme.com"
