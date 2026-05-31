"""Wire models for agent automation runs list/get."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _AutomationRunListItemWire(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    id: str
    workflow_id: str = Field(alias="workflowId")
    temporal_run_id: Optional[str] = Field(default=None, alias="temporalRunId")
    agent_id: int = Field(alias="agentId")
    agent_name: str = Field(alias="agentName")
    agent_type: str = Field(alias="agentType")
    status: str
    trigger_type: Optional[str] = Field(default=None, alias="triggerType")
    started_at: Optional[datetime] = Field(default=None, alias="startedAt")
    ended_at: Optional[datetime] = Field(default=None, alias="endedAt")
    duration_ms: Optional[int] = Field(default=None, alias="durationMs")
    summary: Optional[str] = None
    pending_approval: Optional[Any] = Field(default=None, alias="pendingApproval")


class _ListAutomationRunsResponseWire(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    runs: List[_AutomationRunListItemWire]
    next_page_token: Optional[str] = Field(default=None, alias="nextPageToken")
    counts: Dict[str, Any]


class _GetAutomationRunResponseWire(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    id: str
    workflow_id: str = Field(alias="workflowId")
    temporal_run_id: Optional[str] = Field(default=None, alias="temporalRunId")
    agent_id: int = Field(alias="agentId")
    agent_name: str = Field(alias="agentName")
    agent_type: str = Field(alias="agentType")
    status: str
    started_at: Optional[datetime] = Field(default=None, alias="startedAt")
    ended_at: Optional[datetime] = Field(default=None, alias="endedAt")
    history: Optional[Any] = None
