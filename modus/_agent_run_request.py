"""Shared agent-host run request helpers (chat + runs.create*)."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Union
from uuid import uuid4

from pydantic import BaseModel


def request_dict(body: Union[BaseModel, Mapping[str, Any]]) -> dict[str, Any]:
    """A request body as its wire dict: a request model by its camelCase aliases, a mapping as is."""
    if isinstance(body, BaseModel):
        return body.model_dump(mode="json", by_alias=True, exclude_none=True)
    return dict(body)


def resolve_agent_run_session_id(session_id: Optional[str] = None) -> str:
    """Mint or reuse a non-empty sessionId for agent-host runs."""
    if isinstance(session_id, str) and session_id.strip():
        return session_id.strip()
    return str(uuid4())


def with_agent_run_session_id(body: Union[BaseModel, Mapping[str, Any]]) -> dict[str, Any]:
    """Copy body and ensure sessionId is set (parity with chat)."""
    out = request_dict(body)
    out["sessionId"] = resolve_agent_run_session_id(
        out.get("sessionId") if isinstance(out.get("sessionId"), str) else None
    )
    return out
