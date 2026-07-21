"""Workflow read types — re-exported from OpenAPI DTOs."""

from __future__ import annotations

from .._generated.models import (
    AgentDto,
    AgentType,
    AgentVariationDto,
    ResourceLifecycleStatus,
    WorkflowDto,
)

Workflow = WorkflowDto
WorkflowStatus = ResourceLifecycleStatus
WorkflowVariation = AgentVariationDto
WorkflowType = AgentType
# Deprecated twin of WorkflowDto (same shape). Prefer Workflow.
Agent = AgentDto

__all__ = [
    "Agent",
    "AgentDto",
    "Workflow",
    "WorkflowDto",
    "WorkflowStatus",
    "WorkflowType",
    "WorkflowVariation",
]
