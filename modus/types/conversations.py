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

__all__ = [
    "Conversation",
    "ConversationDto",
    "ConversationListItem",
    "ConversationListItemDto",
    "ConversationMessageDto",
    "Message",
]
