"""Skill read types — deprecated aliases of OpenAPI ``SkillDto``."""

from __future__ import annotations

from .scopes import (
    AccessConfigDto,
    ScopeStatus,
    ScopeVariation,
    SkillDto,
)

# Deprecated twin schema (same shape as ScopeDto). Prefer Scope / ScopeDto.
Skill = SkillDto
SkillStatus = ScopeStatus
SkillVariation = ScopeVariation

__all__ = ["AccessConfigDto", "Skill", "SkillStatus", "SkillVariation", "SkillDto"]
