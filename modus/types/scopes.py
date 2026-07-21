"""Scope read types — re-exported from OpenAPI DTOs."""

from __future__ import annotations

from .._generated.models import (
    AccessConfigDto,
    ResourceLifecycleStatus,
    ScopeDto,
    SkillDto,
    SkillVariationDto,
)

Scope = ScopeDto
ScopeStatus = ResourceLifecycleStatus
ScopeVariation = SkillVariationDto
# Deprecated twin of ScopeDto (same shape). Prefer Scope.
Skill = SkillDto

__all__ = [
    "AccessConfigDto",
    "Scope",
    "ScopeDto",
    "ScopeStatus",
    "ScopeVariation",
    "Skill",
    "SkillDto",
]
