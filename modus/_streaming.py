"""
SSE stream parser.

parse_sse_stream() converts raw SSE lines into typed RunEvent objects.

Events and their handling:
    token          -> TokenEvent  (yielded to text_stream; sub-agent tokens carry sub_agent)
    done           -> DoneEvent   (ends iteration; carries the final answer in content)
    node_content   -> the wrapped workflow node frame (a node's done/error/cancelled/stream_timeout is dropped)
    workflow_done  -> DoneEvent   (content = finalOutput)
    workflow_error -> ErrorEvent; workflow_cancelled -> CancelledEvent
    approval_required -> ApprovalRequiredEvent
    error          -> ErrorEvent  (raised as ModusError)
    cancelled      -> CancelledEvent (raised as RunCancelledError)
    stream_timeout -> StreamTimeoutEvent (raised as StreamTimeoutError)
    all others     -> silently ignored
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterator, Optional

from .types.runs import (
    ApprovalRequiredEvent,
    AssistantContentResetEvent,
    CancelledEvent,
    DoneEvent,
    ErrorEvent,
    RunEvent,
    StreamTimeoutEvent,
    TokenEvent,
)


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
        if data is not None:
            yield from _parse_data(data)


def _optional_str(value: Any) -> Optional[str]:
    return value if isinstance(value, str) else None


_NODE_TERMINAL_TYPES = frozenset({"done", "error", "cancelled", "stream_timeout"})


def _parse_data(data: Dict[str, Any]) -> Iterator[RunEvent]:
    event_type = data.get("type", "unknown")

    if event_type == "node_content":
        # A workflow wraps each node's frames; the inner frame is a normal run event.
        # A node's own terminal frame does not end the workflow: only workflow_* does.
        inner = data.get("event")
        if isinstance(inner, dict) and inner.get("type") not in _NODE_TERMINAL_TYPES:
            yield from _parse_data(inner)
    elif event_type == "token":
        yield TokenEvent(content=data.get("content", ""), sub_agent=_optional_str(data.get("subAgent")))
    elif event_type in ("done", "workflow_done"):
        content = data.get("content") if event_type == "done" else data.get("finalOutput")
        yield DoneEvent(
            run_id=data.get("runId", ""),
            thread_id=data.get("threadId", ""),
            content=_optional_str(content),
        )
    elif event_type == "approval_required":
        yield ApprovalRequiredEvent(
            tool_id=_optional_str(data.get("toolId")),
            tool_name=_optional_str(data.get("toolName")),
            title=_optional_str(data.get("title")),
            description=_optional_str(data.get("description")),
            args=data.get("args") if isinstance(data.get("args"), dict) else None,
            node_id=_optional_str(data.get("nodeId")),
            prompt=_optional_str(data.get("prompt")),
            options=data.get("options") if isinstance(data.get("options"), list) else None,
        )
    elif event_type == "workflow_cancelled":
        yield CancelledEvent()
    elif event_type in ("error", "workflow_error"):
        msg = (
            data.get("error")
            or data.get("message")
            or data.get("content")
            or "Unknown run error"
        )
        yield ErrorEvent(message=str(msg))
    elif event_type == "cancelled":
        yield CancelledEvent()
    elif event_type == "stream_timeout":
        yield StreamTimeoutEvent()
    elif event_type == "assistant_content_reset":
        content = data.get("content")
        if not isinstance(content, str):
            return
        yield AssistantContentResetEvent(
            content=content,
            visible_content=(
                str(data["visibleContent"])
                if isinstance(data.get("visibleContent"), str)
                else None
            ),
            attempt=(int(data["attempt"]) if isinstance(data.get("attempt"), int) else 1),
            reason=(
                str(data["reason"])
                if isinstance(data.get("reason"), str)
                else "provider_stream_failed"
            ),
            sub_agent=data["subAgent"] if isinstance(data.get("subAgent"), dict) else None,
        )
    # Everything else (keepalives, tool frames, unknown future types) is
    # ignored for forward compatibility.
