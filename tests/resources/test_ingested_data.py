"""Tests for client.ingested_data."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from modus import AsyncModus, ConflictError, Modus

BASE = "https://api.test"
KEY = "modus_test_ingested_data"


@respx.mock
def test_upload_http_preserves_exact_strings_and_wire_names() -> None:
    route = respx.post(f"{BASE}/api/v1/ingested-data").mock(
        return_value=httpx.Response(
            201,
            json={"checksum": "a" * 64},
        )
    )
    client = Modus(api_key=KEY, base_url=BASE, max_retries=0)

    result = client.ingested_data.upload(
        integration_type="postgresql",
        request={
            "type": "http",
            "uri": "https://example.com/שלום?q=%20",
            "method": "PATCH",
            "body": "",
        },
        response={"status": 200, "format": "text", "content": "line 1\r\nשלום\r\n"},
    )

    assert result.checksum == "a" * 64
    assert json.loads(route.calls[0].request.content) == {
        "integration_type": "postgresql",
        "request": {
            "type": "http",
            "uri": "https://example.com/שלום?q=%20",
            "method": "PATCH",
            "body": "",
        },
        "response": {"status": 200, "format": "text", "content": "line 1\r\nשלום\r\n"},
    }


@pytest.mark.asyncio
@respx.mock
async def test_async_upload_sql_preserves_empty_response() -> None:
    route = respx.post(f"{BASE}/api/v1/ingested-data").mock(
        return_value=httpx.Response(
            201,
            json={"checksum": "b" * 64},
        )
    )
    async with AsyncModus(api_key=KEY, base_url=BASE, max_retries=0) as client:
        result = await client.ingested_data.upload(
            integration_type="snowflake",
            request={"type": "sql", "query": "SELECT 1\n"},
            response={"format": "csv", "content": ""},
        )

    assert result.checksum == "b" * 64
    assert json.loads(route.calls[0].request.content)["response"]["content"] == ""


@respx.mock
def test_duplicate_raises_standard_conflict_error_without_retry() -> None:
    route = respx.post(f"{BASE}/api/v1/ingested-data").mock(
        return_value=httpx.Response(
            409,
            json={"message": "Identical ingested data already exists"},
        )
    )
    client = Modus(api_key=KEY, base_url=BASE, max_retries=2)

    with pytest.raises(ConflictError, match="already exists"):
        client.ingested_data.upload(
            integration_type="snowflake",
            request={"type": "sql", "query": "SELECT 1"},
            response={"format": "csv", "content": ""},
        )

    assert route.call_count == 1
