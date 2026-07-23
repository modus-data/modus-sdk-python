"""Workflow read types — re-exported from OpenAPI DTOs."""

from __future__ import annotations

from .._generated.models import (
    AgentType,
    AgentVariationDto,
    ResourceLifecycleStatus,
    WorkflowDto,
)

Workflow = WorkflowDto
WorkflowStatus = ResourceLifecycleStatus
WorkflowVariation = AgentVariationDto
WorkflowType = AgentType
# Deprecated product name. Prefer Workflow.
Agent = WorkflowDto

__all__ = [
    "Agent",
    "Workflow",
    "WorkflowDto",
    "WorkflowStatus",
    "WorkflowType",
    "WorkflowVariation",
]
