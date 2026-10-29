"""SSE event types for chat streaming."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Union

# ---------------------------------------------------------------------------
# SSE event types — used by _streaming.py
# ---------------------------------------------------------------------------


@dataclass
class TokenEvent:
    """A streaming text chunk from the skill."""

    type: Literal["token"] = field(default="token", init=False)
    content: str = ""
    sub_agent: Optional[str] = None
    """Set when a sub-agent produced the token; None for the assistant's own reply."""
    id: Optional[str] = None
    """The SSE event id. Pass it as ``last_event_id`` to ``runs.stream`` to resume after this event."""


@dataclass
class DoneEvent:
    """The run completed successfully."""

    type: Literal["done"] = field(default="done", init=False)
    run_id: str = ""
    thread_id: str = ""
    content: Optional[str] = None
    """The run's final answer."""
    id: Optional[str] = None
    """The SSE event id. Pass it as ``last_event_id`` to ``runs.stream`` to resume after this event."""


@dataclass
class ErrorEvent:
    """The run failed with an error."""

    type: Literal["error"] = field(default="error", init=False)
    message: str = ""
    request_id: Optional[str] = None
    """The id to quote to support for this failure."""
    id: Optional[str] = None
    """The SSE event id. Pass it as ``last_event_id`` to ``runs.stream`` to resume after this event."""


@dataclass
class CancelledEvent:
    """The run was cancelled."""

    type: Literal["cancelled"] = field(default="cancelled", init=False)
    id: Optional[str] = None
    """The SSE event id. Pass it as ``last_event_id`` to ``runs.stream`` to resume after this event."""


@dataclass
class StreamTimeoutEvent:
    """The stream timed out without a terminal event."""

    type: Literal["stream_timeout"] = field(default="stream_timeout", init=False)
    id: Optional[str] = None
    """The SSE event id. Pass it as ``last_event_id`` to ``runs.stream`` to resume after this event."""


@dataclass
class AssistantContentResetEvent:
    """Replace content emitted by a failed provider attempt."""

    type: Literal["assistant_content_reset"] = field(default="assistant_content_reset", init=False)
    content: str = ""
    visible_content: Optional[str] = None
    attempt: int = 1
    reason: str = "provider_stream_failed"
    sub_agent: Optional[Dict[str, Any]] = None
    """Set when the reset belongs to a sub-agent's timeline; None for the assistant's own reply."""
    id: Optional[str] = None
    """The SSE event id. Pass it as ``last_event_id`` to ``runs.stream`` to resume after this event."""


@dataclass
class ApprovalRequiredEvent:
    """The run stopped for a human decision.

    A write tool needs approval (``tool_id``, ``tool_name``, ``title``,
    ``description``, ``args``), or a workflow approval node is waiting
    (``node_id``, ``prompt``, ``options``).
    """

    type: Literal["approval_required"] = field(default="approval_required", init=False)
    tool_id: Optional[str] = None
    tool_name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    args: Optional[Dict[str, Any]] = None
    node_id: Optional[str] = None
    prompt: Optional[str] = None
    options: Optional[List[Dict[str, str]]] = None
    id: Optional[str] = None
    """The SSE event id. Pass it as ``last_event_id`` to ``runs.stream`` to resume after this event."""


# Union of all event types the _streaming.py parser can produce.
RunEvent = Union[
    TokenEvent,
    DoneEvent,
    ErrorEvent,
    CancelledEvent,
    StreamTimeoutEvent,
    AssistantContentResetEvent,
    ApprovalRequiredEvent,
]
