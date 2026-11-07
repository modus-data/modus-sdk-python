"""
W3C trace context for SDK requests.

Every request carries a ``traceparent``, so one id names a call on both sides: the trace id
comes back on errors as ``ModusError.trace_id``, and the server continues that trace. The
retry loop keeps one trace id for a call and its re-sends; each send gets its own span id.
"""

from __future__ import annotations

import re
import secrets
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Dict, Iterator, Optional, Tuple

_TRACEPARENT = re.compile(r"^[0-9a-f]{2}-([0-9a-f]{32})-[0-9a-f]{16}-[0-9a-f]{2}$")

# (trace id, sends before this one) of the call the retry loop is sending.
_call: ContextVar[Optional[Tuple[str, int]]] = ContextVar("modus_call_trace", default=None)


def new_trace_id() -> str:
    return secrets.token_hex(16)


def trace_id_of(value: Optional[str]) -> Optional[str]:
    """The trace id a ``traceparent`` names, or None when it is not one."""
    match = _TRACEPARENT.match(value or "")
    return match.group(1) if match else None


@contextmanager
def call_send(trace_id: str, resend: int) -> Iterator[None]:
    """Mark the requests sent inside as send ``resend`` (0 first) of the call ``trace_id``."""
    token = _call.set((trace_id, resend))
    try:
        yield
    finally:
        _call.reset(token)


def request_headers() -> Dict[str, str]:
    """
    A ``traceparent`` (not sampled: the SDK records no spans) for one request, in the
    current call's trace or a new one, plus ``X-Modus-Retry-Attempt`` on a re-send.
    """
    trace_id, resend = _call.get() or (new_trace_id(), 0)
    headers = {"traceparent": f"00-{trace_id}-{secrets.token_hex(8)}-00"}
    if resend:
        headers["X-Modus-Retry-Attempt"] = str(resend)
    return headers
