"""
Conversation types.

Two shapes are returned by the conversations API:

- ConversationListItem  — from GET /api/v1/skills/:id/conversations (list)
  Lightweight summary: firstMessage, messageCount, userIds. No messages array.

- Conversation          — from GET /api/v1/skills/:id/conversations/:threadId (get)
  Full thread with the complete messages array.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel

from .tool_calls import ToolCall


class Message(BaseModel):
    """
    A single message in a conversation thread.

    The API uses ``type`` ("human", "ai", "tool") rather than a ``role`` field.
    ``tool_calls`` contains any tool invocations made by the assistant turn.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    type: Optional[str] = None        # "human", "ai", "tool", "system"
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    id: Optional[str] = None

    @field_validator("tool_calls", mode="before")
    @classmethod
    def _coerce_tool_calls(cls, value: object) -> object:
        if value is None or (
            isinstance(value, list) and value and isinstance(value[0], ToolCall)
        ):
            return value
        if isinstance(value, list):
            return [ToolCall.model_validate(item) for item in value]
        return value


class ConversationListItem(BaseModel):
    """
    Lightweight conversation summary returned by the list endpoint.

    Use ``client.skills.conversations.get(skill_id, thread_id)`` to fetch
    the full message history for a thread.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    thread_id: str
    skill_id: int
    first_message: Optional[str] = None
    """The text of the first user message in the thread."""
    title: Optional[str] = None
    """User-set or auto-generated title, if any."""
    message_count: int = 0
    """Total number of messages (human + AI turns) in the thread."""
    created_at: datetime
    updated_at: datetime
    user_ids: List[str] = []
    """Clerk user IDs of participants in this thread."""


class Conversation(BaseModel):
    """
    Full conversation thread with all messages.

    Returned by ``client.skills.conversations.get(skill_id, thread_id)``.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    thread_id: str
    skill_id: int
    messages: List[Message] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
