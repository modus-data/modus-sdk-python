"""Agent read types — re-exported from OpenAPI DTOs."""

from __future__ import annotations

from .._generated.models import AgentDto, AgentType, AgentVariationDto, ResourceLifecycleStatus

Agent = AgentDto
AgentStatus = ResourceLifecycleStatus
AgentVariation = AgentVariationDto

__all__ = [
    "Agent",
    "AgentDto",
    "AgentStatus",
    "AgentType",
    "AgentVariation",
]
