"""Conversation types — re-exported from OpenAPI DTOs."""

from __future__ import annotations

from .._generated.models import (
    ConversationDto,
    ConversationListItemDto,
    ConversationMessageDto,
)

Conversation = ConversationDto
ConversationListItem = ConversationListItemDto
Message = ConversationMessageDto


def conversation_skill_id(item: ConversationListItem) -> int | None:
    """Return skill id for a conversation list item, or None for direct Modus (skill_id 0)."""
    skill_id = item.skill_id
    return None if skill_id is None or skill_id == 0 else int(skill_id)


__all__ = [
    "Conversation",
    "ConversationDto",
    "ConversationListItem",
    "ConversationListItemDto",
    "ConversationMessageDto",
    "Message",
    "conversation_skill_id",
]
