"""Tests for mgmt.tools.list."""

import httpx
import pytest
import respx
from modus.management import AsyncModusManagement, ModusManagement

BASE = "https://api.modus.com"

TOOLS_PAGE_1 = {
    "tools": [{"id": "web_search", "displayName": "Web Search", "requiresConnection": False}],
    "nextPageToken": "cur_1",
}

TOOLS_PAGE_2 = {
    "tools": [{"id": "slack", "displayName": "Slack", "requiresConnection": True}],
    "nextPageToken": None,
}


def _client():
    return ModusManagement(api_key="modus_test_key", base_url=BASE)


@respx.mock
def test_tools_list():
    route = respx.get(f"{BASE}/api/v1/tools").mock(return_value=httpx.Response(200, json=TOOLS_PAGE_1))
    page = _client().tools.list()
    assert len(page.items) == 1
    assert page.items[0].id == "web_search"
    assert page.items[0].requires_connection is False
    assert page.next_page_token == "cur_1"
    params = dict(route.calls[0].request.url.params)
    assert params["pageSize"] == "25"


@respx.mock
def test_tools_list_paginates():
    respx.get(f"{BASE}/api/v1/tools").mock(
        side_effect=[
            httpx.Response(200, json=TOOLS_PAGE_1),
            httpx.Response(200, json=TOOLS_PAGE_2),
        ]
    )
    client = _client()
    page1 = client.tools.list(page_size=1)
    assert page1.next_page_token == "cur_1"
    page2 = page1.get_next_page()
    assert page2.items[0].id == "slack"
    assert page2.next_page_token is None


@respx.mock
@pytest.mark.asyncio
async def test_tools_list_async():
    respx.get(f"{BASE}/api/v1/tools").mock(return_value=httpx.Response(200, json=TOOLS_PAGE_1))
    async with AsyncModusManagement(api_key="modus_test_key", base_url=BASE) as client:
        page = await client.tools.list()
    assert page.items[0].id == "web_search"
