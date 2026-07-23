"""Shared agent-host run request helpers (chat_stream + runs.create*)."""

from __future__ import annotations

from typing import Any, Mapping, Optional
from uuid import uuid4


def resolve_agent_run_session_id(session_id: Optional[str] = None) -> str:
    """Mint or reuse a non-empty sessionId for agent-host runs."""
    if isinstance(session_id, str) and session_id.strip():
        return session_id.strip()
    return str(uuid4())


def with_agent_run_session_id(body: Mapping[str, Any]) -> dict[str, Any]:
    """Copy body and ensure sessionId is set (parity with chat_stream)."""
    out: dict[str, Any] = dict(body)
    out["sessionId"] = resolve_agent_run_session_id(
        out.get("sessionId") if isinstance(out.get("sessionId"), str) else None
    )
    return out
