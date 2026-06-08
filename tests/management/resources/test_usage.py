"""Tests for mgmt.usage.list."""

import httpx
import pytest
import respx
from modus.management import AsyncModusManagement, ModusManagement
from modus.management.types.usage import UsageReport

BASE = "https://api.modus.com"

USAGE_RESP = {
    "org_id": "org_abc123",
    "since": "2026-05-01T00:00:00.000Z",
    "until": "2026-05-08T00:00:00.000Z",
    "rollup": "hour",
    "buckets": [
        {
            "bucket": "2026-05-01T00:00:00.000Z",
            "model": "claude-sonnet-4-5",
            "callCount": 12,
            "inputTokens": 4000,
            "outputTokens": 900,
        }
    ],
    "totals": {"callCount": 12, "inputTokens": 4000, "outputTokens": 900},
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
