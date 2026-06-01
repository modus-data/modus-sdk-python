"""Public types for agent automation runs."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .json_blob import JsonObject


class AgentRunListItem(BaseModel):
    """Summary row from GET /api/v1/agents/{id}/runs."""

    model_config = ConfigDict(extra="forbid")

    id: str
    workflow_id: str
    temporal_run_id: Optional[str] = None
    agent_id: int
    agent_name: str
    agent_type: str
    status: str
    trigger_type: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    summary: Optional[str] = None
    pending_approval: Optional[JsonObject] = None


class AgentRunListPage(BaseModel):
    """Paginated list of agent automation runs."""

    model_config = ConfigDict(extra="forbid")

    runs: List[AgentRunListItem]
    next_page_token: Optional[str] = None
    counts: JsonObject = Field(default_factory=JsonObject)


class AgentRun(BaseModel):
    """Full run payload from GET /api/v1/agents/{id}/runs/{runId}."""

    model_config = ConfigDict(extra="allow")

    id: str
    workflow_id: str
    temporal_run_id: Optional[str] = None
    agent_id: int
    agent_name: str
    agent_type: str
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    history: Optional[List[JsonObject]] = None
