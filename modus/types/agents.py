"""Agent read types — deprecated aliases of Workflow."""

from __future__ import annotations

from .workflows import (
    Agent,
    WorkflowDto,
    WorkflowStatus,
    WorkflowType,
    WorkflowVariation,
)

AgentStatus = WorkflowStatus
AgentType = WorkflowType
AgentVariation = WorkflowVariation

__all__ = [
    "Agent",
    "AgentStatus",
    "AgentType",
    "AgentVariation",
    "WorkflowDto",
]
