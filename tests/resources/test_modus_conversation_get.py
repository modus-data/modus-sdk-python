"""Conversation detail response and identifier behavior on both Python clients."""

import json

import httpx
import pytest
import respx
from modus import AsyncModus, Modus
from modus.types.conversations import Conversation
from pydantic import ValidationError

BASE = "https://api.modus.com"
CONVERSATION = {
    "threadId": "thread-1", "scopeId": 0,
    "messages": [{"type": "human", "content": "Hello"}],
    "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z",
}


@pytest.mark.parametrize("is_async", [False, True])
@pytest.mark.parametrize("body", [CONVERSATION, None, [], 42])
@respx.mock
async def test_conversation_get_validates_the_response_model(is_async, body):
    client = (AsyncModus if is_async else Modus)(api_key="modus_test_key", base_url=BASE)
    route = respx.get(f"{BASE}/api/v1/modus/conversations/thread-1").mock(
        return_value=httpx.Response(
            200, content=json.dumps(body), headers={"content-type": "application/json"},
        )
    )
    try:
        if body is CONVERSATION:
            result = client.modus.conversations.get("thread-1")
            if is_async:
                result = await result
            assert isinstance(result, Conversation)
            assert result.thread_id == "thread-1"
            assert result.messages[0].content == "Hello"
        else:
            with pytest.raises(ValidationError):
                result = client.modus.conversations.get("thread-1")
                if is_async:
                    await result
        assert route.call_count == 1
    finally:
        if is_async:
            await client.aclose()
        else:
            client.close()


@pytest.mark.parametrize("is_async", [False, True])
@respx.mock
async def test_conversation_get_rejects_empty_thread_id_before_http(is_async):
    client = (AsyncModus if is_async else Modus)(api_key="modus_test_key", base_url=BASE)
    route = respx.get(f"{BASE}/api/v1/modus/conversations/")
    try:
        with pytest.raises(ValueError, match="thread_id"):
            result = client.modus.conversations.get("")
            if is_async:
                await result
        assert not route.called
    finally:
        if is_async:
            await client.aclose()
        else:
            client.close()
