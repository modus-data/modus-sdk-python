"""Agent read types — deprecated aliases of OpenAPI ``AgentDto``."""

from __future__ import annotations

from .workflows import (
    AgentDto,
    WorkflowStatus,
    WorkflowType,
    WorkflowVariation,
)

# Deprecated twin schema (same shape as WorkflowDto). Prefer Workflow / WorkflowDto.
Agent = AgentDto
AgentStatus = WorkflowStatus
AgentType = WorkflowType
AgentVariation = WorkflowVariation

__all__ = [
    "Agent",
    "AgentDto",
    "AgentStatus",
    "AgentType",
    "AgentVariation",
]
