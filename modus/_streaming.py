"""
SSE stream parser.

parse_sse_stream() converts raw SSE lines into typed RunEvent objects; each event
carries the SSE ``id`` that preceded it (pass it to ``runs.stream(last_event_id=...)``).

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
from typing import Any, AsyncIterator, Dict, Iterator, Optional

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


def _optional_str(value: Any) -> Optional[str]:
    return value if isinstance(value, str) else None


_NODE_TERMINAL_TYPES = frozenset({"done", "error", "cancelled", "stream_timeout"})


def _events(data: Dict[str, Any], event_id: Optional[str]) -> Iterator[RunEvent]:
    event_type = data.get("type", "unknown")

    if event_type == "node_content":
        # A workflow wraps each node's frames; the inner frame is a normal run event.
        # A node's own terminal frame does not end the workflow: only workflow_* does.
        inner = data.get("event")
        if isinstance(inner, dict) and inner.get("type") not in _NODE_TERMINAL_TYPES:
            yield from _events(inner, event_id)
    elif event_type == "token":
        yield TokenEvent(
            content=data.get("content", ""),
            sub_agent=_optional_str(data.get("subAgent")),
            id=event_id,
        )
    elif event_type in ("done", "workflow_done"):
        content = data.get("content") if event_type == "done" else data.get("finalOutput")
        yield DoneEvent(
            run_id=data.get("runId", ""),
            thread_id=data.get("threadId", ""),
            content=_optional_str(content),
            id=event_id,
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
            id=event_id,
        )
    elif event_type in ("error", "workflow_error"):
        msg = data.get("error") or data.get("message") or data.get("content") or "Unknown run error"
        yield ErrorEvent(
            message=str(msg),
            request_id=_optional_str(data.get("requestId")),
            id=event_id,
        )
    elif event_type in ("cancelled", "workflow_cancelled"):
        yield CancelledEvent(id=event_id)
    elif event_type == "stream_timeout":
        yield StreamTimeoutEvent(id=event_id)
    elif event_type == "assistant_content_reset":
        content = data.get("content")
        if not isinstance(content, str):
            return
        yield AssistantContentResetEvent(
            content=content,
            visible_content=(
                str(data["visibleContent"]) if isinstance(data.get("visibleContent"), str) else None
            ),
            attempt=(int(data["attempt"]) if isinstance(data.get("attempt"), int) else 1),
            reason=(
                str(data["reason"])
                if isinstance(data.get("reason"), str)
                else "provider_stream_failed"
            ),
            sub_agent=data["subAgent"] if isinstance(data.get("subAgent"), dict) else None,
            id=event_id,
        )
    # Keepalives, tool and progress events, and unknown future types yield nothing.


class SseParser:
    """
    Line-at-a-time SSE parser. An ``id:`` line names every event after it until the
    next ``id:`` line, so one parser must see every line of a stream.
    """

    def __init__(self) -> None:
        self._last_id: Optional[str] = None

    def feed(self, line: str) -> Iterator[RunEvent]:
        if line.startswith("id:"):
            self._last_id = line[3:].strip() or None
            return iter(())
        data = _parse_line(line)
        return iter(()) if data is None else _events(data, self._last_id)


def parse_sse_stream(lines: Iterator[str]) -> Iterator[RunEvent]:
    """
    Convert a raw SSE line iterator into typed RunEvent objects, each carrying its
    SSE ``id``.

    Silently drops keepalive and unrecognized event types.
    Yields only: TokenEvent, DoneEvent, ErrorEvent, CancelledEvent,
    StreamTimeoutEvent, AssistantContentResetEvent, ApprovalRequiredEvent.
    """
    parser = SseParser()
    for line in lines:
        yield from parser.feed(line)


async def parse_sse_stream_async(lines: AsyncIterator[str]) -> AsyncIterator[RunEvent]:
    """Async :func:`parse_sse_stream`."""
    parser = SseParser()
    async for line in lines:
        for event in parser.feed(line):
            yield event
