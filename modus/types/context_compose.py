"""Skill context composition — re-exported from OpenAPI DTOs."""

from __future__ import annotations

from .._generated.models import (
    ComposeSkillContextRequestDto,
    ComposeSkillContextResponseDto,
)

SkillContextComposition = ComposeSkillContextResponseDto
ComposeSkillContextRequest = ComposeSkillContextRequestDto

__all__ = [
    "ComposeSkillContextRequest",
    "ComposeSkillContextRequestDto",
    "ComposeSkillContextResponseDto",
    "SkillContextComposition",
]
