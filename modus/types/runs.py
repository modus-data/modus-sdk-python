"""SSE event types for chat streaming."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

# ---------------------------------------------------------------------------
# SSE event types — used by _streaming.py
# ---------------------------------------------------------------------------


@dataclass
class TokenEvent:
    """A streaming text chunk from the skill."""

    type: str = field(default="token", init=False)
    content: str = ""
    sub_agent: Optional[str] = None
    """Set when a sub-agent produced the token; None for the assistant's own reply."""


@dataclass
class DoneEvent:
    """The run completed successfully."""

    type: str = field(default="done", init=False)
    run_id: str = ""
    thread_id: str = ""
    content: Optional[str] = None
    """The run's final answer."""


@dataclass
class ErrorEvent:
    """The run failed with an error."""

    type: str = field(default="error", init=False)
    message: str = ""


@dataclass
class CancelledEvent:
    """The run was cancelled."""

    type: str = field(default="cancelled", init=False)


@dataclass
class StreamTimeoutEvent:
    """The stream timed out without a terminal event."""

    type: str = field(default="stream_timeout", init=False)


@dataclass
class AssistantContentResetEvent:
    """Replace content emitted by a failed provider attempt."""

    type: str = field(default="assistant_content_reset", init=False)
    content: str = ""
    visible_content: Optional[str] = None
    attempt: int = 1
    reason: str = "provider_stream_failed"
    sub_agent: Optional[Dict[str, Any]] = None
    """Set when the reset belongs to a sub-agent's timeline; None for the assistant's own reply."""


@dataclass
class ApprovalRequiredEvent:
    """The run stopped for a human decision.

    A write tool needs approval (``tool_id``, ``tool_name``, ``title``,
    ``description``, ``args``), or a workflow approval node is waiting
    (``node_id``, ``prompt``, ``options``).
    """

    type: str = field(default="approval_required", init=False)
    tool_id: Optional[str] = None
    tool_name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    args: Optional[Dict[str, Any]] = None
    node_id: Optional[str] = None
    prompt: Optional[str] = None
    options: Optional[List[Dict[str, str]]] = None


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
