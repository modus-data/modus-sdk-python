"""Conversation types — identical shape to the consumption SDK."""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class Message(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")
    type: Optional[str] = None
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    id: Optional[str] = None


class ConversationListItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")
    thread_id: str
    skill_id: int
    first_message: Optional[str] = None
    title: Optional[str] = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime
    user_ids: List[str] = []


class Conversation(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")
    thread_id: str
    skill_id: int
    messages: List[Message] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
