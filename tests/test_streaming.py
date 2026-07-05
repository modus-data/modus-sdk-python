"""Tests for SSE stream parsing."""

from modus._streaming import parse_sse_stream
from modus.types.runs import (
    CancelledEvent,
    DoneEvent,
    ErrorEvent,
    StreamTimeoutEvent,
    TokenEvent,
)


def lines(*parts):
    return iter(parts)


def test_token_event():
    events = list(parse_sse_stream(lines('data: {"type":"token","content":"Hello"}')))
    assert len(events) == 1
    assert isinstance(events[0], TokenEvent)
    assert events[0].content == "Hello"


def test_multiple_token_events():
    events = list(parse_sse_stream(lines(
        'data: {"type":"token","content":"Hello"}',
        'data: {"type":"token","content":" world"}',
    )))
    assert [e.content for e in events] == ["Hello", " world"]


def test_done_event():
    events = list(parse_sse_stream(lines('data: {"type":"done","runId":"run-123"}')))
    assert len(events) == 1
    assert isinstance(events[0], DoneEvent)
    assert events[0].run_id == "run-123"


def test_done_event_includes_thread_id():
    events = list(
        parse_sse_stream(
            lines(
                'data: {"type":"done","runId":"run-123",'
                '"threadId":"thread-456"}'
            )
        )
    )
    assert events[0].thread_id == "thread-456"


def test_error_event_uses_error_field():
    events = list(
        parse_sse_stream(lines('data: {"type":"error","error":"Quota exceeded"}'))
    )
    assert isinstance(events[0], ErrorEvent)
    assert events[0].message == "Quota exceeded"


def test_error_event():
    events = list(parse_sse_stream(lines('data: {"type":"error","message":"Something broke"}')))
    assert len(events) == 1
    assert isinstance(events[0], ErrorEvent)
    assert events[0].message == "Something broke"


def test_cancelled_event():
    events = list(parse_sse_stream(lines('data: {"type":"cancelled"}')))
    assert isinstance(events[0], CancelledEvent)


def test_stream_timeout_event():
    events = list(parse_sse_stream(lines('data: {"type":"stream_timeout"}')))
    assert isinstance(events[0], StreamTimeoutEvent)


def test_heartbeat_silently_ignored():
    events = list(parse_sse_stream(lines('data: {"type":"heartbeat"}')))
    assert events == []


def test_ws_chunk_silently_ignored():
    events = list(parse_sse_stream(lines('data: {"type":"ws_chunk","content":"x"}')))
    assert events == []


def test_tool_start_ignored_in_v1():
    events = list(parse_sse_stream(lines('data: {"type":"tool_start","tool":"sql_query"}')))
    assert events == []


def test_agent_thinking_ignored_in_v1():
    events = list(parse_sse_stream(lines('data: {"type":"agent_thinking","content":"..."}')))
    assert events == []


def test_unknown_event_type_ignored():
    events = list(parse_sse_stream(lines('data: {"type":"future_event_type","data":"x"}')))
    assert events == []


def test_non_data_lines_ignored():
    events = list(parse_sse_stream(lines(
        ": keep-alive comment",
        "",
        "event: message",
        'data: {"type":"token","content":"hi"}',
    )))
    assert len(events) == 1
    assert events[0].content == "hi"


def test_invalid_json_ignored():
    events = list(parse_sse_stream(lines("data: not-valid-json")))
    assert events == []


def test_done_sentinel_ignored():
    events = list(parse_sse_stream(lines("data: [DONE]")))
    assert events == []


def test_mixed_stream():
    stream = lines(
        'data: {"type":"token","content":"The "}',
        'data: {"type":"agent_thinking","content":"reasoning..."}',
        'data: {"type":"token","content":"answer"}',
        'data: {"type":"heartbeat"}',
        'data: {"type":"done","runId":"run-abc"}',
    )
    events = list(parse_sse_stream(stream))
    assert len(events) == 3  # 2 tokens + 1 done (heartbeat and thinking ignored)
    assert isinstance(events[0], TokenEvent)
    assert isinstance(events[1], TokenEvent)
    assert isinstance(events[2], DoneEvent)
