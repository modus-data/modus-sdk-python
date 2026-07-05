"""Tests for mgmt.organization.delete."""

import httpx
import pytest
import respx
from modus.management import AsyncModusManagement, ModusManagement

BASE = "https://api.modus.com"


def _client():
    return ModusManagement(api_key="modus_test_key", base_url=BASE)


@respx.mock
def test_organization_delete():
    route = respx.delete(f"{BASE}/api/v1/users/organization").mock(
        return_value=httpx.Response(204)
    )
    _client().organization.delete()
    assert route.called


@respx.mock
@pytest.mark.asyncio
async def test_organization_delete_async():
    route = respx.delete(f"{BASE}/api/v1/users/organization").mock(
        return_value=httpx.Response(204)
    )
    async with AsyncModusManagement(api_key="modus_test_key", base_url=BASE) as client:
        await client.organization.delete()
    assert route.called
