"""Skill read types — deprecated aliases of Scope."""

from __future__ import annotations

from .scopes import (
    AccessConfigDto,
    ScopeDto,
    ScopeStatus,
    ScopeVariation,
    Skill,
)

SkillStatus = ScopeStatus
SkillVariation = ScopeVariation

__all__ = [
    "AccessConfigDto",
    "Skill",
    "SkillStatus",
    "SkillVariation",
    "ScopeDto",
]
