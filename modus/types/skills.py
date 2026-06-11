"""Skill read types — re-exported from OpenAPI DTOs."""

from __future__ import annotations

from .._generated.models import (
    AccessConfigDto,
    SkillDto,
    SkillVariationDto,
    Status1,
)

Skill = SkillDto
SkillStatus = Status1
SkillVariation = SkillVariationDto

__all__ = ["AccessConfigDto", "Skill", "SkillStatus", "SkillVariation", "SkillDto"]
