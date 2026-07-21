"""Conversation types — re-exported from OpenAPI DTOs."""

from __future__ import annotations

from .._deprecation import warn_deprecated
from .._generated.models import (
    ConversationDto,
    ConversationListItemDto,
    ConversationMessageDto,
)

Conversation = ConversationDto
ConversationListItem = ConversationListItemDto
Message = ConversationMessageDto


def conversation_scope_id(item: ConversationListItem) -> int | None:
    """Return scope id for a conversation list item, or None for direct Modus (id 0)."""
    scope_id = item.scope_id if item.scope_id is not None else item.skill_id
    return None if scope_id is None or scope_id == 0 else int(scope_id)


def conversation_skill_id(item: ConversationListItem) -> int | None:
    """Deprecated. Use :func:`conversation_scope_id` instead."""
    warn_deprecated(old="conversation_skill_id", new="conversation_scope_id")
    return conversation_scope_id(item)


__all__ = [
    "Conversation",
    "ConversationDto",
    "ConversationListItem",
    "ConversationListItemDto",
    "ConversationMessageDto",
    "Message",
    "conversation_scope_id",
    "conversation_skill_id",
]
