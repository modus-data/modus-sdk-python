"""Scope read types — re-exported from OpenAPI DTOs."""

from __future__ import annotations

from .._generated.models import (
    AccessConfigDto,
    ResourceLifecycleStatus,
    ScopeDto,
    SkillVariationDto,
)

Scope = ScopeDto
ScopeStatus = ResourceLifecycleStatus
ScopeVariation = SkillVariationDto
# Deprecated product name. Prefer Scope.
Skill = ScopeDto

__all__ = [
    "AccessConfigDto",
    "Scope",
    "ScopeDto",
    "ScopeStatus",
    "ScopeVariation",
    "Skill",
]
