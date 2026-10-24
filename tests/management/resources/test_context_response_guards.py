"""Context response validation is preserved on both generated client flavors."""

import json

import httpx
import pytest
import respx
from modus.management import AsyncModusManagement, ModusManagement
from pydantic import ValidationError

BASE = "https://api.modus.com"
CASES = [
    ("files", "get", ("upload-1",)),
    ("elements", "list", ()),
    ("elements", "get", ("element-1",)),
    ("dashboards", "list_versions", ("dash-1",)),
    ("dashboards", "list_draft_snapshots", ("dash-1",)),
    ("dashboards", "get_version", ("dash-1", "version-1")),
    ("dashboards", "restore_version", ("dash-1", "version-1")),
    ("dashboards", "cancel_ownership_transfer", ("dash-1",)),
    ("dashboards", "accept_ownership_transfer", ("dash-1",)),
]


@pytest.mark.parametrize("resource,method,args", CASES)
@pytest.mark.parametrize("body", [None, [], "invalid", 42, False])
@respx.mock
def test_sync_rejects_non_object_success(resource, method, args, body):
    respx.route().mock(return_value=httpx.Response(200, content=json.dumps(body)))
    with ModusManagement(api_key="modus_test_key", base_url=BASE, max_retries=0) as client:
        target = (
            client.context.dashboards.elements("dash-1")
            if resource == "elements"
            else getattr(client.context, resource)
        )
        with pytest.raises(ValidationError):
            getattr(target, method)(*args)


@pytest.mark.asyncio
@pytest.mark.parametrize("resource,method,args", CASES)
@pytest.mark.parametrize("body", [None, [], "invalid", 42, False])
@respx.mock
async def test_async_rejects_non_object_success(resource, method, args, body):
    respx.route().mock(return_value=httpx.Response(200, content=json.dumps(body)))
    async with AsyncModusManagement(api_key="modus_test_key", base_url=BASE, max_retries=0) as client:
        target = (
            client.context.dashboards.elements("dash-1")
            if resource == "elements"
            else getattr(client.context, resource)
        )
        with pytest.raises(ValidationError):
            await getattr(target, method)(*args)
