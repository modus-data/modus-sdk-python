"""SSE event types for chat streaming."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

# ---------------------------------------------------------------------------
# SSE event types — used by _streaming.py
# ---------------------------------------------------------------------------


@dataclass
class TokenEvent:
    """A streaming text chunk from the skill."""

    type: str = field(default="token", init=False)
    content: str = ""


@dataclass
class DoneEvent:
    """The run completed successfully."""

    type: str = field(default="done", init=False)
    run_id: str = ""
    thread_id: str = ""


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


# Union of all event types the _streaming.py parser can produce.
RunEvent = Union[
    TokenEvent,
    DoneEvent,
    ErrorEvent,
    CancelledEvent,
    StreamTimeoutEvent,
    AssistantContentResetEvent,
]
