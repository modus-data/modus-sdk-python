"""Chat types — re-exported from OpenAPI DTOs."""

from __future__ import annotations

from .._generated.models import SkillChatRequestDto, SkillChatResponseDto

ChatResult = SkillChatResponseDto

__all__ = ["ChatResult", "SkillChatRequestDto", "SkillChatResponseDto"]
