"""chat() on scopes, workflows and Modus streams from the agent host."""

from __future__ import annotations

import json
from typing import AsyncIterator, Iterator

import httpx
import pytest
import respx
from modus import AsyncModus, Modus, ModusError, ValidationError
from modus._chat import AsyncChatSession, ChatSession, _ChatRequest

API = "https://api.getmodus.com"
AGENT = "https://agent.getmodus.com"
MODEL = "claude-sonnet-5.5"

ANSWER_FRAMES = [
    {"type": "token", "content": "Let me check. "},
    {"type": "tool_start", "tool": {"toolId": "t1", "toolName": "sql"}},
    {"type": "token", "content": "chatter", "subAgent": "researcher"},
    {"type": "tool_end", "tool": {"toolId": "t1", "toolName": "sql", "success": True}},
    {"type": "token", "content": "Revenue grew 12% QoQ."},
    {"type": "done", "runId": "run-1", "threadId": "thread-1", "content": "Revenue grew 12% QoQ."},
]


def sse(frames: list) -> httpx.Response:
    body = "".join(f"id: 1-0\ndata: {json.dumps(frame)}\n\n" for frame in frames)
    return httpx.Response(200, text=body, headers={"Content-Type": "text/event-stream"})


def sent(route: respx.Route, call: int = 0) -> dict:
    return json.loads(route.calls[call].request.content)


@pytest.fixture
def client() -> Modus:
    return Modus(api_key="modus_test_key_chat", base_url=API, max_retries=0)


@respx.mock
def test_chat_result_is_server_final_answer(client: Modus) -> None:
    respx.post(f"{AGENT}/agent/v1/scopes/199/runs").mock(return_value=sse(ANSWER_FRAMES))

    result = client.scopes.chat(199, "Revenue trend?", model=MODEL).result()

    assert (result.content, result.thread_id, result.run_id) == ("Revenue grew 12% QoQ.", "thread-1", "run-1")


@respx.mock
def test_text_stream_top_level_only(client: Modus) -> None:
    respx.post(f"{AGENT}/agent/v1/scopes/199/runs").mock(return_value=sse(ANSWER_FRAMES))

    with client.scopes.chat(199, "Revenue trend?", model=MODEL) as chat:
        tokens = list(chat.text_stream)

    assert tokens == ["Let me check. ", "Revenue grew 12% QoQ."]


@respx.mock
def test_chat_posts_agent_host_with_session_id(client: Modus) -> None:
    route = respx.post(f"{AGENT}/agent/v1/scopes/199/runs").mock(return_value=sse(ANSWER_FRAMES))

    client.scopes.chat(199, "Follow up", model=MODEL, thread_id="api-skill-199-abc").result()

    assert sent(route) == {
        "message": "Follow up",
        "config": {"model": MODEL},
        "sessionId": "api-skill-199-abc",
        "streamProtocolVersion": 2,
    }


@respx.mock
def test_buffered_era_thread_id_continues(client: Modus) -> None:
    route = respx.post(f"{AGENT}/agent/v1/modus/runs").mock(return_value=sse(ANSWER_FRAMES))

    client.modus.chat("And then?", model=MODEL, thread_id="agent_0_abc").result()

    assert sent(route)["sessionId"] == "agent_0_abc"


@respx.mock
def test_approval_and_resume(client: Modus) -> None:
    respx.post(f"{AGENT}/agent/v1/modus/runs").mock(
        return_value=sse(
            [
                {"type": "approval_required", "toolId": "tool-9", "toolName": "run_sql_write", "title": "Update 3 rows"},
                {"type": "done", "runId": "run-1", "threadId": "thread-1", "content": ""},
            ]
        )
    )
    resume = respx.post(f"{AGENT}/agent/v1/runs/run-1/resume").mock(
        return_value=sse([{"type": "done", "runId": "run-2", "threadId": "thread-1", "content": "Updated."}])
    )

    chat = client.modus.chat("Fix the typo", model=MODEL)
    first = chat.result()
    done = chat.resume(decision="approve").result()

    assert first.approval is not None and first.approval.tool_name == "run_sql_write"
    assert sent(resume) == {"sessionId": "thread-1", "decision": "approve", "streamProtocolVersion": 2}
    assert "message" not in sent(resume)
    assert done.content == "Updated."


SCOPE_PAUSED = [
    {"type": "approval_required", "toolId": "tool-9", "toolName": "post_comment", "args": {"project_id": 0}},
    {"type": "done", "runId": "run-1", "threadId": "agent_1553_t1", "content": ""},
]


@respx.mock
def test_scope_chat_resumes_on_the_run_route_with_its_scope_thread(client: Modus) -> None:
    respx.post(f"{AGENT}/agent/v1/scopes/1553/runs").mock(return_value=sse(SCOPE_PAUSED))
    resume = respx.post(f"{AGENT}/agent/v1/runs/run-1/resume").mock(
        return_value=sse([{"type": "done", "runId": "run-2", "threadId": "agent_1553_t1", "content": "Denied."}])
    )

    chat = client.scopes.chat(1553, "Post the test comment.", model=MODEL)
    assert chat.result().approval is not None
    done = chat.resume(decision="deny").result()

    assert sent(resume) == {"sessionId": "agent_1553_t1", "decision": "deny", "streamProtocolVersion": 2}
    assert done.content == "Denied."


@respx.mock
async def test_async_scope_chat_resumes_on_the_run_route_with_its_scope_thread() -> None:
    respx.post(f"{AGENT}/agent/v1/scopes/1553/runs").mock(return_value=sse(SCOPE_PAUSED))
    resume = respx.post(f"{AGENT}/agent/v1/runs/run-1/resume").mock(
        return_value=sse([{"type": "done", "runId": "run-2", "threadId": "agent_1553_t1", "content": "Approved."}])
    )
    client = AsyncModus(api_key="modus_test_key_chat", base_url=API, max_retries=0)

    chat = client.scopes.chat(1553, "Post the test comment.", model=MODEL)
    await chat
    done = await chat.resume(decision="approve")

    assert sent(resume) == {"sessionId": "agent_1553_t1", "decision": "approve", "streamProtocolVersion": 2}
    assert done.content == "Approved."


@respx.mock
@pytest.mark.parametrize("run_id", ["..", ".", " "])
def test_resume_refuses_a_run_id_that_is_not_one_path_segment(client: Modus, run_id: str) -> None:
    start = respx.post(f"{AGENT}/agent/v1/modus/runs").mock(
        return_value=sse(
            [
                {"type": "approval_required", "toolId": "tool-9"},
                {"type": "done", "runId": run_id, "threadId": "thread-1", "content": ""},
            ]
        )
    )

    chat = client.modus.chat("Fix the typo", model=MODEL)
    chat.result()

    with pytest.raises(ValidationError):
        chat.resume(decision="approve")
    assert respx.calls.call_count == start.call_count == 1


@respx.mock
def test_iterating_twice_sends_one_request(client: Modus) -> None:
    route = respx.post(f"{AGENT}/agent/v1/scopes/199/runs").mock(return_value=sse(ANSWER_FRAMES))

    chat = client.scopes.chat(199, "Revenue trend?", model=MODEL)
    first = list(chat.text_stream)
    second = list(chat.text_stream)

    assert second == first
    assert chat.result().content == "Revenue grew 12% QoQ."
    assert route.call_count == 1


@respx.mock
def test_workflow_chat_streams_node_tokens(client: Modus) -> None:
    respx.post(f"{AGENT}/agent/v1/workflows/7/runs").mock(
        return_value=sse(
            [
                {"type": "workflow_started", "runId": "wf-1", "automationId": 7},
                {"type": "node_content", "nodeId": "n1", "event": {"type": "token", "content": "Weekly "}},
                {"type": "node_content", "nodeId": "n1", "event": {"type": "token", "content": "digest"}},
                {"type": "workflow_done", "runId": "wf-1", "finalOutput": "Weekly digest"},
            ]
        )
    )

    chat = client.workflows.chat(7, "Run it", model=MODEL, thread_id="wf-thread")
    tokens = list(chat.text_stream)
    result = chat.result()

    assert tokens == ["Weekly ", "digest"]
    assert (result.content, result.thread_id, result.run_id) == ("Weekly digest", "wf-thread", "wf-1")


@pytest.mark.parametrize(
    "inner",
    [
        {"type": "done", "runId": "child-1", "content": "node one only"},
        {"type": "error", "error": "node timed out"},
        {"type": "cancelled", "runIds": ["child-1"]},
        {"type": "stream_timeout"},
    ],
)
@respx.mock
def test_workflow_chat_ignores_a_node_terminal_frame(client: Modus, inner: dict) -> None:
    # A node's own terminal frame arrives wrapped in node_content; only workflow_* ends the session.
    respx.post(f"{AGENT}/agent/v1/workflows/7/runs").mock(
        return_value=sse(
            [
                {"type": "node_content", "nodeId": "n1", "event": {"type": "token", "content": "one "}},
                {"type": "node_content", "nodeId": "n1", "event": inner},
                {"type": "node_content", "nodeId": "n2", "event": {"type": "token", "content": "two"}},
                {"type": "workflow_done", "runId": "wf-1", "finalOutput": "final"},
            ]
        )
    )

    chat = client.workflows.chat(7, "Run it", model=MODEL)
    tokens = list(chat.text_stream)
    result = chat.result()

    assert tokens == ["one ", "two"]
    assert (result.content, result.run_id) == ("final", "wf-1")


@respx.mock
def test_workflow_error_raises(client: Modus) -> None:
    respx.post(f"{AGENT}/agent/v1/workflows/7/runs").mock(
        return_value=sse([{"type": "workflow_error", "runId": "wf-1", "error": "Node n1 failed: quota"}])
    )

    with pytest.raises(ModusError, match="quota"):
        client.workflows.chat(7, "Run it", model=MODEL).result()


def test_local_base_url_refuses_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MODUS_AGENT_HOST", raising=False)
    client = Modus(api_key="modus_test_key_chat", base_url="http://localhost:3040", max_retries=0)

    with pytest.raises(ModusError, match="agent_host"):
        client.scopes.chat(1, "x", model=MODEL)


def test_unsupported_model_rejected(client: Modus) -> None:
    with pytest.raises(ValueError, match="Unsupported model"):
        client.scopes.chat(1, "x", model="not-a-model")


def test_no_chat_stream(client: Modus) -> None:
    assert not hasattr(client.scopes, "chat_stream")
    assert not hasattr(client.modus, "chat_stream")
    assert not hasattr(client.workflows, "chat_stream")


@respx.mock
async def test_async_chat_is_awaitable() -> None:
    respx.post(f"{AGENT}/agent/v1/scopes/199/runs").mock(return_value=sse(ANSWER_FRAMES))
    client = AsyncModus(api_key="modus_test_key_chat", base_url=API, max_retries=0)

    result = await client.scopes.chat(199, "Revenue trend?", model=MODEL)

    assert result.content == "Revenue grew 12% QoQ."


@respx.mock
async def test_async_text_stream() -> None:
    respx.post(f"{AGENT}/agent/v1/modus/runs").mock(return_value=sse(ANSWER_FRAMES))
    client = AsyncModus(api_key="modus_test_key_chat", base_url=API, max_retries=0)

    async with client.modus.chat("Revenue trend?", model=MODEL) as chat:
        tokens = [token async for token in chat.text_stream]

    assert tokens == ["Let me check. ", "Revenue grew 12% QoQ."]


@pytest.mark.parametrize("field", ["content", "thread_id", "run_id", "approval"])
def test_buffered_era_result_fields_name_the_migration(client: Modus, field: str) -> None:
    chat = client.scopes.chat(199, "Revenue trend?", model=MODEL)

    with pytest.raises(AttributeError, match=rf"\.result\(\)\.{field}"):
        getattr(chat, field)


@respx.mock
async def test_sync_and_async_sessions_share_the_result_accessor() -> None:
    respx.post(f"{AGENT}/agent/v1/scopes/199/runs").mock(side_effect=[sse(ANSWER_FRAMES), sse(ANSWER_FRAMES)])
    sync = Modus(api_key="modus_test_key_chat", base_url=API, max_retries=0)
    async_client = AsyncModus(api_key="modus_test_key_chat", base_url=API, max_retries=0)

    sync_result = sync.scopes.chat(199, "Revenue trend?", model=MODEL).result()
    async_result = await async_client.scopes.chat(199, "Revenue trend?", model=MODEL).result()

    assert sync_result == async_result
    assert async_result.content == "Revenue grew 12% QoQ."
    with pytest.raises(AttributeError, match=r"\(await chat\)\.content"):
        async_client.scopes.chat(199, "Revenue trend?", model=MODEL).content  # noqa: B018


RESET_FRAMES = [
    {"type": "token", "content": "Draft "},
    {"type": "token", "content": "garbled"},
    {"type": "assistant_content_reset", "content": "Draft ", "attempt": 2, "reason": "provider_stream_failed"},
    {"type": "assistant_content_reset", "content": "zzz", "attempt": 2, "subAgent": {"name": "researcher"}},
    {"type": "token", "content": "final."},
    {"type": "done", "runId": "run-1", "threadId": "thread-1", "content": "Draft final."},
]


@respx.mock
def test_text_stream_after_result_replays_a_top_level_reset(client: Modus) -> None:
    respx.post(f"{AGENT}/agent/v1/scopes/199/runs").mock(return_value=sse(RESET_FRAMES))

    chat = client.scopes.chat(199, "Hi", model=MODEL)
    chat.result()

    assert "".join(chat.text_stream) == "Draft final."


@respx.mock
async def test_async_text_stream_after_await_replays_a_top_level_reset() -> None:
    respx.post(f"{AGENT}/agent/v1/scopes/199/runs").mock(return_value=sse(RESET_FRAMES))
    chat = AsyncModus(api_key="modus_test_key_chat", base_url=API, max_retries=0).scopes.chat(199, "Hi", model=MODEL)

    await chat

    assert "".join([token async for token in chat.text_stream]) == "Draft final."


class _OpenStream:
    """A server that keeps the connection open after its frames; records whether the SDK let go."""

    def __init__(self, frames: list) -> None:
        self.lines = [f"data: {json.dumps(frame)}" for frame in frames]
        self.released = False

    def stream_post(self, path: str, json: dict) -> Iterator[str]:  # noqa: A002
        try:
            yield from self.lines
            yield "data: {\"type\": \"token\", \"content\": \"never read\"}"
        finally:
            self.released = True

    async def astream_post(self, path: str, json: dict) -> AsyncIterator[str]:  # noqa: A002
        try:
            for line in self.lines:
                yield line
            yield "data: {\"type\": \"token\", \"content\": \"never read\"}"
        finally:
            self.released = True


_DONE_ONLY = [{"type": "done", "runId": "run-1", "threadId": "thread-1", "content": "Hi."}]
_REQUEST = _ChatRequest(path="/agent/v1/modus/runs", body={"message": "Hi"}, session_id="thread-1")


def test_a_consumer_that_stops_at_done_releases_the_connection() -> None:
    server = _OpenStream(_DONE_ONLY)
    chat = ChatSession(server, _REQUEST)  # type: ignore[arg-type]

    for event in chat.event_stream:
        if event.type == "done":
            break

    assert server.released
    assert chat.result().content == "Hi."


async def test_async_consumer_that_stops_at_done_releases_the_connection() -> None:
    server = _OpenStream(_DONE_ONLY)
    server.stream_post = server.astream_post  # type: ignore[method-assign]
    chat = AsyncChatSession(server, _REQUEST)  # type: ignore[arg-type]

    async for event in chat.event_stream:
        if event.type == "done":
            break

    assert server.released
    assert (await chat.result()).content == "Hi."
