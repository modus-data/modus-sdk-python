"""
SSE stream parser.

parse_sse_stream() converts raw SSE lines into typed RunEvent objects.

Events and their handling:
    token          -> TokenEvent  (yielded to text_stream)
    done           -> DoneEvent   (ends iteration, populates RunResult)
    error          -> ErrorEvent  (raised as ModusError)
    cancelled      -> CancelledEvent (raised as RunCancelledError)
    stream_timeout -> StreamTimeoutEvent (raised as StreamTimeoutError)
    all others     -> silently ignored
"""

from __future__ import annotations
import json
from typing import Iterator, Optional, Dict, Any

from .types.runs import (
    CancelledEvent,
    DoneEvent,
    ErrorEvent,
    RunEvent,
    StreamTimeoutEvent,
    TokenEvent,
)

_SILENTLY_IGNORED = frozenset({
    "heartbeat",
    "ws_chunk",
    "unknown",
    "tool_start",
    "tool_end",
    "tool_chunk",
    "agent_thinking",
    "warning",
    "selected_final_content",
})


def _parse_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single SSE line. Returns the parsed JSON payload or None.
    SSE lines that carry data start with "data: ".
    """
    if not line.startswith("data: "):
        return None
    raw = line[6:].strip()
    if not raw or raw == "[DONE]":
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def parse_sse_stream(lines: Iterator[str]) -> Iterator[RunEvent]:
    """
    Convert a raw SSE line iterator into typed RunEvent objects.

    Silently drops keepalive and unrecognized event types.
    Yields only: TokenEvent, DoneEvent, ErrorEvent, CancelledEvent,
    StreamTimeoutEvent.
    """
    for line in lines:
        data = _parse_line(line)
        if data is None:
            continue

        event_type = data.get("type", "unknown")

        if event_type == "token":
            yield TokenEvent(content=data.get("content", ""))
        elif event_type == "done":
            yield DoneEvent(run_id=data.get("runId", ""))
        elif event_type == "error":
            msg = data.get("message") or data.get("content") or "Unknown run error"
            yield ErrorEvent(message=str(msg))
        elif event_type == "cancelled":
            yield CancelledEvent()
        elif event_type == "stream_timeout":
            yield StreamTimeoutEvent()
        elif event_type in _SILENTLY_IGNORED:
            continue
        # Truly unknown types: silently ignored for forward compatibility
