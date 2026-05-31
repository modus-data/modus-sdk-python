"""Public types for skill/agent chat."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChatResult:
    """Buffered chat response."""

    text: str
    thread_id: str
    run_id: str
