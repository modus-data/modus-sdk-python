"""Agent read types — re-exported from OpenAPI DTOs."""

from __future__ import annotations

from .._generated.models import AgentDto, AgentVariationDto, Status1, Type2

Agent = AgentDto
AgentStatus = Status1
AgentType = Type2
AgentVariation = AgentVariationDto

__all__ = [
    "Agent",
    "AgentDto",
    "AgentStatus",
    "AgentType",
    "AgentVariation",
]
