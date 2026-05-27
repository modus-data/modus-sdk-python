"""
Types for skill run results and SSE events.

INTERNAL — not part of the public API in v0.2. This module is scaffolding for
the future skills.run/stream feature, which depends on a backend operation
that does not yet exist in the OpenAPI spec. These types are intentionally
not re-exported from `modus.types` or `modus`.

See docs/DEVELOPMENT.md (v0.3 prerequisites) and docs/SSE_DESIGN_NOTES.md
(SDK-side design conventions for when the spec lands).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Union


@dataclass
class RunResult:
    """The complete result of a skill run."""

    text: str
    """The full text response from the skill."""

    run_id: str
    """The unique run identifier. Useful for support and debugging."""


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


# Union of all event types the _streaming.py parser can produce.
RunEvent = Union[TokenEvent, DoneEvent, ErrorEvent, CancelledEvent, StreamTimeoutEvent]
