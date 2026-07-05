"""Regression: uid path params must be URL-encoded in context items methods."""
import httpx
import respx
from modus import Modus

TEST_KEY = "modus_test_key_abc123"
BASE = "https://api.modus.com"

from tests.fixtures.api_shapes import SAMPLE_CONTEXT_ITEM

ITEM_RESPONSE = {**SAMPLE_CONTEXT_ITEM, "uid": "test-uid"}


def _client():
    return Modus(api_key=TEST_KEY, base_url=BASE)


@respx.mock
def test_items_get_url_encodes_uid():
    uid = "uid with spaces"
    route = respx.get(f"{BASE}/api/v1/context/items/uid%20with%20spaces").mock(
        return_value=httpx.Response(200, json={**ITEM_RESPONSE, "uid": uid})
    )
    _client().context.items.get(uid)
    assert route.called


@respx.mock
def test_items_get_normal_uuid_still_works(client, sample_context_item):
    uid = sample_context_item["uid"]
    respx.get(f"{BASE}/api/v1/context/items/{uid}").mock(
        return_value=httpx.Response(200, json=sample_context_item)
    )
    item = client.context.items.get(uid)
    assert item.uid == uid
